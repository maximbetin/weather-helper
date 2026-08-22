import test from "node:test";
import assert from "node:assert/strict";
import { ForecastViewModel } from "../js/view_model.js";
import { createDailyReport } from "../js/core/models.js";
import { createHour, madridInstant } from "./helpers.js";

const DATE = "2099-06-10";

function rankableForecast(locationName) {
  const hours = [10, 11, 12].map((hour) => createHour(madridInstant(2099, 6, 10, hour), 12));
  return { daily_forecasts: { [DATE]: hours }, day_scores: { [DATE]: createDailyReport(DATE, hours, locationName) } };
}

// Hours outside the daylight window produce no daily report, so the location is
// loaded and inspectable but never ranked.
function unrankableForecast() {
  const hours = [22, 23].map((hour) => createHour(madridInstant(2099, 6, 10, hour), 12));
  return { daily_forecasts: { [DATE]: hours }, day_scores: {} };
}

function viewModelWith(forecasts) {
  const vm = new ForecastViewModel();
  vm.forecasts = forecasts;
  vm.selectedDate = DATE;
  return vm;
}

test("allLocations lists every loaded location, ranked ones first", () => {
  const vm = viewModelWith({ gijon: rankableForecast("Gijón"), llanes: unrankableForecast() });

  const all = vm.allLocations();
  assert.deepEqual(
    all.map((item) => item.locationKey),
    ["gijon", "llanes"],
  );
  assert.equal(all[0].isRanked, true);
  assert.equal(all[0].rank, 1);
  // The unranked one still names itself and stays selectable for hourly detail.
  assert.equal(all[1].isRanked, false);
  assert.equal(all[1].rank, null);
  assert.equal(all[1].normalizedScore, null);
  assert.equal(all[1].bestWindow, "");
  assert.ok(vm.availableLocationKeys().includes("llanes"));
  assert.ok(vm.hourlyForecast("llanes").length > 0);
});

test("hourly rows omit precipitation probability only when the forecast has none", () => {
  const withProbability = createHour(madridInstant(2099, 6, 10, 10), 12, { precipitation_probability: 40 });
  const vm = viewModelWith({ gijon: { daily_forecasts: { [DATE]: [withProbability] }, day_scores: {} } });

  assert.equal(vm._hourlyForecastView(withProbability).precipitationProbability, "40%");
  assert.equal(vm._hourlyForecastView(createHour(madridInstant(2099, 6, 10, 11), 12)).precipitationProbability, null);
});

test("hourly rows expose profile-aware color ratings for displayed measurements", () => {
  const hour = createHour(madridInstant(2099, 6, 10, 10), 12, {
    temp: 24,
    wind: 10,
    cloud_coverage: 75,
    precipitation_amount: 0,
    relative_humidity: 65,
  });
  const vm = viewModelWith({ gijon: { daily_forecasts: { [DATE]: [hour] }, day_scores: {} } });
  const metrics = Object.fromEntries(vm._hourlyForecastView(hour).metrics.map((metric) => [metric.label, metric.rating]));

  assert.deepEqual(metrics, {
    Temp: "Excellent",
    Wind: "Poor",
    Clouds: "Fair",
    Rain: "Excellent",
    Humidity: "Very Good",
  });
});
