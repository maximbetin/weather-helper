import test from "node:test";
import assert from "node:assert/strict";
import { createDailyReport } from "../js/core/models.js";
import { madridInstant, createHour } from "./helpers.js";

test("daily report with empty daylight hours", () => {
  const testDate = "2024-03-15";
  const report = createDailyReport(testDate, [], "Test Location");

  assert.equal(report.date, testDate);
  assert.equal(report.location_name, "Test Location");
  assert.equal(report.avg_score, -Infinity);
  assert.equal(report.likely_rain_hours, 0);
  assert.equal(report.min_temp, null);
  assert.equal(report.max_temp, null);
  assert.equal(report.avg_temp, null);
});

test("daily report calculations", () => {
  const testDate = "2024-03-15";
  const hours = [
    createHour(madridInstant(2024, 3, 15, 8), null, {
      temp: 20, wind: 5, cloud_coverage: 20, precipitation_amount: 0.0,
      temp_score: 6, wind_score: -3, cloud_score: 3, precip_amount_score: 4,
    }),
    createHour(madridInstant(2024, 3, 15, 9), null, {
      temp: 22, wind: 6, cloud_coverage: 30, precipitation_amount: 0.0,
      temp_score: 6, wind_score: -3, cloud_score: 2, precip_amount_score: 4,
    }),
    createHour(madridInstant(2024, 3, 15, 10), null, {
      temp: 21, wind: 7, cloud_coverage: 50, precipitation_amount: 0.0,
      temp_score: 6, wind_score: -3, cloud_score: 0, precip_amount_score: 2,
    }),
    createHour(madridInstant(2024, 3, 15, 11), null, {
      temp: 19, wind: 8, cloud_coverage: 80, precipitation_amount: 1.0,
      temp_score: 4, wind_score: -5, cloud_score: -2, precip_amount_score: -3,
    }),
    createHour(madridInstant(2024, 3, 15, 12), null, {
      temp: 18, wind: 9, cloud_coverage: 90, precipitation_amount: 2.0,
      temp_score: 4, wind_score: -5, cloud_score: -4, precip_amount_score: -6,
    }),
  ];

  const report = createDailyReport(testDate, hours, "Test Location");

  assert.equal(report.date, testDate);
  assert.equal(report.location_name, "Test Location");
  assert.equal(report.likely_rain_hours, 2);
  assert.equal(report.min_temp, 18);
  assert.equal(report.max_temp, 22);
  assert.equal(report.avg_temp, 20);

  const expectedScores = [10, 9, 5, -6, -11];
  const expectedAvg = expectedScores.reduce((a, b) => a + b, 0) / expectedScores.length;
  assert.ok(Math.abs(report.avg_score - expectedAvg) < 0.001);
});

const weatherDescriptionCases = [
  [25, [0.0], "Warm"],
  [20, [0.0], "Pleasant"],
  [15, [0.0], "Cool"],
  [5, [0.0], "Cold"],
  [20, [1.5], "Rain (1h)"],
  [20, [1.0, 2.0], "Rain (2h)"],
  [null, [0.0], "Mixed"],
];

for (const [temp, precipList, expectedDesc] of weatherDescriptionCases) {
  test(`weather description for temp=${temp} precip=${JSON.stringify(precipList)}`, () => {
    const testDate = "2024-03-15";
    const hours = precipList.map((precip, i) =>
      createHour(madridInstant(2024, 3, 15, 8 + i), 4, { temp, precipitation_amount: precip }),
    );
    const report = createDailyReport(testDate, hours, "Test");
    assert.equal(report.weather_description, expectedDesc);
  });
}

test("hourly weather total score calculation", () => {
  const hour = createHour(madridInstant(2024, 3, 15, 10), null, {
    temp_score: 5,
    wind_score: -2,
    cloud_score: 3,
    precip_amount_score: 1,
  });
  assert.equal(hour.total_score, 7);
});

test("hourly weather hour extraction", () => {
  const hour = createHour(madridInstant(2024, 3, 15, 14, 30));
  assert.equal(hour.hour, 14);
});
