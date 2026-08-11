import test from "node:test";
import assert from "node:assert/strict";
import {
  ACTIVITY_BEACH_DAY,
  ACTIVITY_HIKING,
  beachDayScore,
  beachPrecipProbabilityScore,
  getActivityProfileKey,
  getActivityProfileLabel,
  getActivityScore,
  getRatingInfo,
  cloudScore,
  normalizeScore,
  precipAmountScore,
  precipProbabilityScore,
  symbolRiskScore,
  tempScore,
  windScore,
  getValueFromRanges,
} from "../js/core/scoring.js";
import { madridInstant, createHour } from "./helpers.js";

test("tempScore", () => {
  const cases = [
    [22, 7], [19, 6], [25, 6], [16, 4], [28, 4], [12, 2], [31, 1],
    [8, -1], [34, -3], [2, -6], [38, -9], [-2, -9], [50, -15], [null, 0],
  ];
  for (const [temp, expected] of cases) assert.equal(tempScore(temp), expected);
});

test("windScore", () => {
  const cases = [[2, 2], [0.5, 1], [4, 0], [6, -2], [10, -4], [14, -6], [18, -7], [25, -8], [null, 0]];
  for (const [wind, expected] of cases) assert.equal(windScore(wind), expected);
});

test("cloudScore", () => {
  const cases = [[20, 4], [5, 3], [45, 2], [70, 0], [85, -1], [100, -3], [null, 0]];
  for (const [clouds, expected] of cases) assert.equal(cloudScore(clouds), expected);
});

test("precipAmountScore", () => {
  const cases = [[0, 5], [0.05, 4], [0.3, 2], [0.7, 0], [1.5, -2], [3.5, -4], [7.5, -6], [15, -8], [25, -12], [null, 0]];
  for (const [precip, expected] of cases) assert.equal(precipAmountScore(precip), expected);
});

test("beachDayScore rewards calm sunny warm weather", () => {
  assert.equal(beachDayScore(27, 2, 5, 0, 60), 26);
});

test("beachDayScore penalizes windy overcast weather", () => {
  assert.equal(beachDayScore(20, 10, 100, 0, 60), -1);
});

test("beachDayScore penalizes rain risk and symbols", () => {
  assert.equal(beachDayScore(27, 2, 5, 0, 60, 70, "rainshowers_day"), 7);
});

test("precipitation probability scoring is profile aware", () => {
  assert.equal(precipProbabilityScore(45), -3);
  assert.equal(beachPrecipProbabilityScore(45), -7);
});

test("symbol risk scoring is profile aware", () => {
  assert.equal(symbolRiskScore("thunderstorm", ACTIVITY_HIKING), -12);
  assert.equal(symbolRiskScore("thunderstorm", ACTIVITY_BEACH_DAY), -16);
});

test("activity profile labels round trip", () => {
  assert.equal(getActivityProfileLabel(ACTIVITY_HIKING), "Hiking");
  assert.equal(getActivityProfileKey("Beach"), ACTIVITY_BEACH_DAY);
  assert.equal(getActivityProfileKey("Unknown"), ACTIVITY_BEACH_DAY);
});

test("activity score uses the selected profile", () => {
  const hour = createHour(madridInstant(2024, 3, 15, 12), 12, {
    temp: 27,
    wind: 2,
    cloud_coverage: 5,
    precipitation_amount: 0,
    relative_humidity: 60,
  });
  assert.equal(getActivityScore(hour, ACTIVITY_HIKING), 12);
  assert.equal(getActivityScore(hour, ACTIVITY_BEACH_DAY), 26);
});

test("activity score applies risk to hiking", () => {
  const hour = createHour(madridInstant(2024, 3, 15, 12), 12, {
    precipitation_probability: 60,
    symbol_code: "rain",
  });
  assert.equal(getActivityScore(hour, ACTIVITY_HIKING), 2);
});

test("beach rating and normalization use beach thresholds", () => {
  assert.equal(getRatingInfo(21, ACTIVITY_BEACH_DAY), "Very Good");
  assert.equal(getRatingInfo(22, ACTIVITY_BEACH_DAY), "Excellent");
  assert.equal(normalizeScore(22, ACTIVITY_BEACH_DAY), 90);
  assert.equal(normalizeScore(26, ACTIVITY_BEACH_DAY), 100);
});

test("normalizeScore boundaries for hiking profile", () => {
  const cases = [
    [23, 100], [25, 100], [18, 90], [13, 80], [7, 65], [2, 50],
    [-2, 26], [0, 38], [-5, 8], [-10, 0], [null, 0], [17, 88], [3, 53],
  ];
  for (const [score, expected] of cases) assert.equal(normalizeScore(score, ACTIVITY_HIKING), expected);
});

test("getValueFromRanges matches, respects exclusivity, and falls back", () => {
  const ranges = [
    [[0, 10], "low"],
    [[10, 20], "mid"],
    [null, "default"],
  ];
  assert.equal(getValueFromRanges(5, ranges), "low");
  assert.equal(getValueFromRanges(10, ranges), "mid");
  assert.equal(getValueFromRanges(10, ranges, true), "low");
  assert.equal(getValueFromRanges(999, ranges), "default");
  assert.equal(getValueFromRanges(null, ranges), null);
  assert.equal(getValueFromRanges("nope", ranges), null);
});
