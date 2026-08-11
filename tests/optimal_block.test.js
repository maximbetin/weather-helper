import test from "node:test";
import assert from "node:assert/strict";
import { findOptimalWeatherBlock } from "../js/core/evaluation.js";
import { ACTIVITY_BEACH_DAY, ACTIVITY_HIKING } from "../js/core/scoring.js";
import { madridHourOf } from "../js/core/timezone.js";
import { madridInstant, createHour } from "./helpers.js";

function plusHours(instant, hours) {
  return new Date(instant.getTime() + hours * 60 * 60 * 1000);
}

test("find optimal block with clear winner", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [
    createHour(baseTime, 5),
    createHour(plusHours(baseTime, 1), 8),
    createHour(plusHours(baseTime, 2), 10),
    createHour(plusHours(baseTime, 3), 12),
    createHour(plusHours(baseTime, 4), 9),
    createHour(plusHours(baseTime, 5), 2),
  ];

  let result = findOptimalWeatherBlock(hours, 1, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.ok(result.avg_score >= 8);
  assert.ok(result.duration >= 1);
  assert.ok(result.combined_score > result.avg_score);

  result = findOptimalWeatherBlock(hours, 2, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.ok(result.duration >= 2);
  assert.ok(result.avg_score >= 8);
});

test("find optimal block with long good block", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [
    createHour(baseTime, 8),
    createHour(plusHours(baseTime, 1), 9),
    createHour(plusHours(baseTime, 2), 10),
    createHour(plusHours(baseTime, 3), 11),
    createHour(plusHours(baseTime, 4), 12),
    createHour(plusHours(baseTime, 5), 5),
  ];

  let result = findOptimalWeatherBlock(hours, 1, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.ok(result.avg_score >= 8);
  assert.ok(result.duration >= 1);
  assert.ok(result.combined_score >= result.avg_score);

  result = findOptimalWeatherBlock(hours, 3, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.ok(result.duration >= 3);
  assert.ok(result.avg_score >= 9);
});

test("find optimal block with no good blocks", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [createHour(baseTime, -2), createHour(plusHours(baseTime, 1), -5), createHour(plusHours(baseTime, 2), -3)];

  assert.equal(findOptimalWeatherBlock(hours, 1, ACTIVITY_HIKING), null);
  assert.equal(findOptimalWeatherBlock(hours, 2, ACTIVITY_HIKING), null);
});

test("find optimal block with single best hour", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [
    createHour(baseTime, -20),
    createHour(plusHours(baseTime, 1), -20),
    createHour(plusHours(baseTime, 2), 8),
    createHour(plusHours(baseTime, 3), -20),
  ];

  let result = findOptimalWeatherBlock(hours, 1, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.equal(result.duration, 1);
  assert.equal(madridHourOf(result.start), 12);

  result = findOptimalWeatherBlock(hours, 2, ACTIVITY_HIKING);
  assert.equal(result, null);
});

test("find optimal block empty input", () => {
  assert.equal(findOptimalWeatherBlock([], 1, ACTIVITY_HIKING), null);
  assert.equal(findOptimalWeatherBlock([], 2, ACTIVITY_HIKING), null);
});

test("find optimal block short good block", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [createHour(baseTime, 8), createHour(plusHours(baseTime, 1), 9)];

  let result = findOptimalWeatherBlock(hours, 1, ACTIVITY_HIKING);
  assert.notEqual(result, null);
  assert.equal(result.duration, 2);

  result = findOptimalWeatherBlock(hours, 3, ACTIVITY_HIKING);
  assert.equal(result, null);
});

test("find optimal block uses activity profile", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const windyHikingHour = createHour(baseTime, 20, {
    temp: 20,
    wind: 10,
    cloud_coverage: 100,
    precipitation_amount: 0,
    relative_humidity: 60,
  });
  const beachHour = createHour(plusHours(baseTime, 1), 5, {
    temp: 27,
    wind: 2,
    cloud_coverage: 5,
    precipitation_amount: 0,
    relative_humidity: 60,
  });

  const hikingResult = findOptimalWeatherBlock([windyHikingHour, beachHour], 1, ACTIVITY_HIKING);
  const beachResult = findOptimalWeatherBlock([windyHikingHour, beachHour], 1, ACTIVITY_BEACH_DAY);

  assert.notEqual(hikingResult, null);
  assert.notEqual(beachResult, null);
  assert.equal(madridHourOf(hikingResult.start), 10);
  assert.equal(madridHourOf(beachResult.start), 11);
});

test("find optimal block does not bridge forecast gaps", () => {
  const baseTime = madridInstant(2023, 1, 1, 10);
  const hours = [createHour(baseTime, 8), createHour(plusHours(baseTime, 2), 9)];

  const result = findOptimalWeatherBlock(hours, 2, ACTIVITY_HIKING);
  assert.equal(result, null);
});
