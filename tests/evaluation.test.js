import test from "node:test";
import assert from "node:assert/strict";
import {
  calculateWeatherAverages,
  createHourlyWeatherFromEntry,
  getAvailableDates,
  getTimeBlocksForDate,
  getTopLocationsForDate,
  processForecast,
} from "../js/core/evaluation.js";
import { ACTIVITY_HIKING } from "../js/core/scoring.js";
import { createDailyReport, createHourlyWeather } from "../js/core/models.js";
import { madridHourOf, TIMEZONE, nowInstant } from "../js/core/timezone.js";
import { madridInstant } from "./helpers.js";

function plusHours(instant, hours) {
  return new Date(instant.getTime() + hours * 60 * 60 * 1000);
}

const sampleForecastData = {
  properties: {
    timeseries: [
      {
        time: "2024-03-15T12:00:00Z",
        data: {
          instant: {
            details: { air_temperature: 20, wind_speed: 5, relative_humidity: 60, cloud_area_fraction: 20 },
          },
          next_1_hours: {
            summary: { symbol_code: "clearsky" },
            details: { precipitation_amount: 0, probability_of_precipitation: 0 },
          },
        },
      },
    ],
  },
};

test("timezone constant is Europe/Madrid", () => {
  assert.equal(TIMEZONE, "Europe/Madrid");
  assert.ok(nowInstant() instanceof Date);
});

test("process forecast empty", () => {
  assert.equal(processForecast({}, "Test Location"), null);
  assert.equal(processForecast({ properties: {} }, "Test Location"), null);

  const result = processForecast({ properties: { timeseries: [] } }, "Test Location");
  assert.notEqual(result, null);
  assert.deepEqual(result.daily_forecasts, {});
  assert.deepEqual(result.day_scores, {});
});

test("process forecast with fixture", () => {
  const result = processForecast(sampleForecastData, "Test Location");
  assert.notEqual(result, null);
  assert.ok("daily_forecasts" in result);
  assert.ok("day_scores" in result);
});

test("create hourly weather uses local time and risk fields", () => {
  const hour = createHourlyWeatherFromEntry(sampleForecastData.properties.timeseries[0]);

  assert.equal(madridHourOf(hour.time), 13); // 12:00 UTC is 13:00 in Madrid in March
  assert.equal(hour.hour, 13);
  assert.equal(hour.precipitation_probability, 0);
  assert.equal(hour.symbol_code, "clearsky");
});

test("get available dates", () => {
  assert.deepEqual(getAvailableDates({}), []);
  assert.deepEqual(getAvailableDates({ other_key: {} }), []);

  const testData = {
    daily_forecasts: {
      "2024-03-15": [],
      "2024-03-16": [],
      "2024-03-14": [],
    },
  };
  const dates = getAvailableDates(testData);
  assert.equal(dates.length, 3);
  assert.deepEqual(dates, ["2024-03-14", "2024-03-15", "2024-03-16"]);
});

test("get time blocks for date", () => {
  assert.deepEqual(getTimeBlocksForDate({}, "2024-03-15"), []);
  assert.deepEqual(getTimeBlocksForDate({ other_key: {} }, "2024-03-15"), []);

  const testDate = "2024-03-15";
  const hour1 = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 10),
    temp_score: 1,
    wind_score: 1,
    cloud_score: 1,
    precip_amount_score: 1,
  });
  const hour2 = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 8),
    temp_score: 2,
    wind_score: 2,
    cloud_score: 2,
    precip_amount_score: 2,
  });

  const testData = { daily_forecasts: { [testDate]: [hour1, hour2] } };

  const blocks = getTimeBlocksForDate(testData, testDate);
  assert.equal(blocks.length, 2);
  assert.equal(blocks[0].hour, 8);
  assert.equal(blocks[1].hour, 10);
});

test("calculate weather averages", () => {
  let [avgTemp, avgWind, avgHumidity, avgPrecip] = calculateWeatherAverages([]);
  assert.equal(avgTemp, null);
  assert.equal(avgWind, null);
  assert.equal(avgHumidity, null);
  assert.equal(avgPrecip, null);

  const hour1 = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 10),
    temp: null,
    wind: null,
    relative_humidity: null,
    precipitation_amount: null,
  });
  [avgTemp, avgWind, avgHumidity, avgPrecip] = calculateWeatherAverages([hour1]);
  assert.equal(avgTemp, null);
  assert.equal(avgWind, null);
  assert.equal(avgHumidity, null);
  assert.equal(avgPrecip, null);

  const sampleHourlyWeather = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 12),
    temp: 20,
    wind: 5,
    cloud_coverage: 20,
    precipitation_amount: 0,
    relative_humidity: 60,
    temp_score: 8,
    wind_score: 9,
    cloud_score: 10,
    precip_amount_score: 6,
    humidity_score: 1,
  });
  [avgTemp, avgWind, avgHumidity, avgPrecip] = calculateWeatherAverages([sampleHourlyWeather]);
  assert.equal(avgTemp, 20.0);
  assert.equal(avgWind, 5.0);
  assert.equal(avgHumidity, 60.0);
  assert.equal(avgPrecip, 0.0);

  const hour2 = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 11),
    temp: 22,
    wind: 3,
    relative_humidity: 55,
    precipitation_amount: 0.2,
  });
  const hour3 = createHourlyWeather({
    time: madridInstant(2024, 3, 15, 12),
    temp: null,
    wind: 7,
    relative_humidity: 65,
    precipitation_amount: null,
  });

  [avgTemp, avgWind, avgHumidity, avgPrecip] = calculateWeatherAverages([sampleHourlyWeather, hour2, hour3]);
  assert.equal(avgTemp, 21.0); // (20 + 22) / 2
  assert.equal(avgWind, 5.0); // (5 + 3 + 7) / 3
  assert.equal(avgHumidity, 60.0); // (60 + 55 + 65) / 3
  assert.ok(Math.abs(avgPrecip - 0.1) < 0.000001); // (0.0 + 0.2) / 2
});

test("process forecast complex", () => {
  const mockTimeseries = [
    {
      time: "2024-03-15T10:00:00Z",
      data: {
        instant: { details: { air_temperature: 20, wind_speed: 5, cloud_area_fraction: 30, relative_humidity: 65 } },
        next_1_hours: { details: { precipitation_amount: 0.1 } },
      },
    },
    {
      time: "2024-03-15T11:00:00Z",
      data: {
        instant: { details: { air_temperature: 22, wind_speed: 3, cloud_area_fraction: 20, relative_humidity: 55 } },
        next_1_hours: { details: { precipitation_amount: 0.0 } },
      },
    },
  ];

  const forecastData = { properties: { timeseries: mockTimeseries } };

  const result = processForecast(forecastData, "Test Location");
  assert.notEqual(result, null);
  assert.ok("daily_forecasts" in result);
  assert.ok("day_scores" in result);
});

test("get top locations for date", () => {
  assert.deepEqual(getTopLocationsForDate({}, "2024-03-15"), []);

  const testData = {
    location1: {
      day_scores: { "2024-03-14": null },
      daily_forecasts: { "2024-03-14": [] },
    },
  };
  assert.deepEqual(getTopLocationsForDate(testData, "2024-03-15"), []);
});

test("get top locations for date no data", () => {
  assert.deepEqual(getTopLocationsForDate({}, "2024-03-15"), []);
});

test("get top locations for date less than n", () => {
  const result = getTopLocationsForDate({}, "2024-03-15", 3);
  assert.ok(Array.isArray(result));
});

test("get top locations for date no matching date", () => {
  const testData = {
    loc1: {
      day_scores: { "2024-03-14": "some_score" },
      daily_forecasts: { "2024-03-14": [] },
    },
  };
  assert.deepEqual(getTopLocationsForDate(testData, "2024-03-15"), []);
});

function createHourWithTotalScore(time, totalScore) {
  const base = Math.floor(totalScore / 4);
  const remainder = totalScore - 3 * base;
  return createHourlyWeather({
    time,
    temp: 20,
    wind: 1,
    precipitation_amount: 0.0,
    relative_humidity: 60,
    cloud_coverage: 20,
    temp_score: base,
    wind_score: base,
    cloud_score: base,
    precip_amount_score: remainder,
    humidity_score: 0,
  });
}

function processedLocation(forecastDate, hours, locationName) {
  return {
    daily_forecasts: { [forecastDate]: hours },
    day_scores: { [forecastDate]: createDailyReport(forecastDate, hours, locationName) },
  };
}

test("location ranking favors sustained positive hours", () => {
  const forecastDate = "2030-06-15";
  const baseTime = madridInstant(2030, 6, 15, 10);
  const isolatedHours = [
    createHourWithTotalScore(baseTime, -5),
    createHourWithTotalScore(plusHours(baseTime, 1), 10),
    createHourWithTotalScore(plusHours(baseTime, 2), -5),
  ];
  const sustainedHours = [0, 1, 2, 3, 4].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), 7));
  const allLocations = {
    isolated: processedLocation(forecastDate, isolatedHours, "One okay hour"),
    sustained: processedLocation(forecastDate, sustainedHours, "Five solid hours"),
  };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);

  assert.deepEqual(ranked.map((result) => result.location_key), ["sustained", "isolated"]);
  assert.equal(ranked[0].optimal_block.duration, 5);
  assert.equal(ranked[0].optimal_block.positive_hour_count, 5);
  assert.equal(ranked[1].optimal_block.duration, 1);
});

test("the score shown beside a window is the window's own quality", () => {
  const forecastDate = "2030-06-15";
  const baseTime = madridInstant(2030, 6, 15, 10);
  const briefExcellentHours = [
    createHourWithTotalScore(baseTime, 20),
    createHourWithTotalScore(plusHours(baseTime, 1), -5),
    createHourWithTotalScore(plusHours(baseTime, 2), -5),
    createHourWithTotalScore(plusHours(baseTime, 3), -5),
  ];
  const allLocations = { brief: processedLocation(forecastDate, briefExcellentHours, "Brief excellent window") };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);

  // raw_score is what the UI and the notification normalize, so it must describe
  // the recommended window rather than the washed-out whole-day average.
  assert.equal(ranked[0].raw_score, ranked[0].optimal_block.avg_score);
  assert.equal(ranked[0].raw_score, 20);
  assert.ok(ranked[0].day_avg_score < ranked[0].raw_score);
});

test("locations are ranked by their best usable window, not by the rest of the day", () => {
  const forecastDate = "2030-06-15";
  const baseTime = madridInstant(2030, 6, 15, 10);
  // A long, genuinely good afternoon window followed by a bad evening.
  const goodWindowHours = [
    ...[0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), 18)),
    ...[4, 5, 6, 7].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), -8)),
  ];
  // Mediocre but unbroken all day: a better whole-day average, no better window.
  const flatMediocreHours = [0, 1, 2, 3, 4, 5, 6, 7].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), 6));
  const allLocations = {
    goodWindow: processedLocation(forecastDate, goodWindowHours, "Good window, bad evening"),
    flat: processedLocation(forecastDate, flatMediocreHours, "Mediocre all day"),
  };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);

  assert.equal(ranked[0].location_key, "goodWindow");
  assert.ok(ranked[0].opportunity_score > ranked[1].opportunity_score);
  assert.equal(ranked[0].score, ranked[0].optimal_block.combined_score);
  // The steadier location really does have the better whole day; that is now only
  // a tie-breaker, so it does not override the better opportunity.
  assert.ok(ranked[1].day_context_score > ranked[0].day_context_score);
});

test("the remaining-day score breaks ties between equally good opportunities", () => {
  const forecastDate = "2030-06-15";
  const baseTime = madridInstant(2030, 6, 15, 10);
  const sharedWindow = [0, 1, 2].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), 12));
  // A washed-out hour breaks the day in two, so the identical morning window stays
  // each location's best opportunity and only the rest of the day differs.
  const breakHour = createHourWithTotalScore(plusHours(baseTime, 3), -30);
  const tail = (score) => [4, 5, 6].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), score));
  const allLocations = {
    dullRest: processedLocation(forecastDate, [...sharedWindow, breakHour, ...tail(-1)], "Same window, dull rest"),
    betterRest: processedLocation(forecastDate, [...sharedWindow, breakHour, ...tail(4)], "Same window, better rest"),
  };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);

  assert.equal(ranked[0].opportunity_score, ranked[1].opportunity_score);
  assert.equal(ranked[0].location_key, "betterRest");
  assert.ok(ranked[0].day_context_score > ranked[1].day_context_score);
});

test("past hours do not influence today's score or ranking", (t) => {
  const forecastDate = "2030-06-15";
  const now = madridInstant(2030, 6, 15, 14);
  t.mock.timers.enable({ apis: ["Date"], now });

  const morning = madridInstant(2030, 6, 15, 10);
  const afternoon = madridInstant(2030, 6, 15, 14);
  // Great morning that has already passed, poor remaining afternoon.
  const spentHours = [
    ...[0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(morning, offset), 20)),
    ...[0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(afternoon, offset), 1)),
  ];
  // Unremarkable morning, decent afternoon still ahead.
  const aheadHours = [
    ...[0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(morning, offset), 1)),
    ...[0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(afternoon, offset), 10)),
  ];
  const allLocations = {
    spent: processedLocation(forecastDate, spentHours, "Great morning, already gone"),
    ahead: processedLocation(forecastDate, aheadHours, "Decent afternoon ahead"),
  };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);
  const spent = ranked.find((r) => r.location_key === "spent");

  assert.equal(ranked[0].location_key, "ahead");
  assert.equal(spent.raw_score, 1);
  assert.equal(spent.day_avg_score, 1);
  assert.equal(madridHourOf(spent.optimal_block.start), 14);
});

test("drastic changes reduce the remaining-day score more than consistent weather", () => {
  const forecastDate = "2030-06-15";
  const baseTime = madridInstant(2030, 6, 15, 10);
  const consistentHours = [0, 1, 2, 3].map((offset) => createHourWithTotalScore(plusHours(baseTime, offset), 10));
  const volatileScores = [0, 20, 0, 20];
  const volatileHours = volatileScores.map((score, offset) => createHourWithTotalScore(plusHours(baseTime, offset), score));
  const allLocations = {
    consistent: processedLocation(forecastDate, consistentHours, "Consistent weather"),
    volatile: processedLocation(forecastDate, volatileHours, "Drastic changes"),
  };

  const ranked = getTopLocationsForDate(allLocations, forecastDate, 10, ACTIVITY_HIKING);
  const results = Object.fromEntries(ranked.map((result) => [result.location_key, result]));

  assert.equal(results.consistent.day_avg_score, 10);
  assert.equal(results.volatile.day_avg_score, 10);
  assert.equal(results.consistent.volatility_penalty, 0);
  assert.ok(results.volatile.volatility_penalty > 0);
  assert.ok(results.consistent.day_context_score > results.volatile.day_context_score);
});
