import test from "node:test";
import assert from "node:assert/strict";
import { ASTURIAS_LOCATIONS } from "../js/core/locations.js";
import {
  FORECAST_UNAVAILABLE_MESSAGE,
  GOOD_OPPORTUNITY_THRESHOLD,
  buildDailyRecommendations,
  buildOutlookNotification,
  formatRecommendationLine,
} from "../js/core/daily_summary.js";
import { ACTIVITY_HIKING } from "../js/core/scoring.js";
import { madridInstant } from "./helpers.js";

function rankedResult(locationKey, locationName, rawScore, startHour, endHour = startHour + 2) {
  return {
    location_key: locationKey,
    location_name: locationName,
    raw_score: rawScore,
    optimal_block: {
      start: madridInstant(2026, 8, 6, startHour),
      end: madridInstant(2026, 8, 6, endHour),
    },
  };
}

test("each activity profile gets its own best location, with no priority city", () => {
  const fakeRank = (forecasts, forecastDate, topN, activityProfile) =>
    activityProfile === ACTIVITY_HIKING
      ? [rankedResult("llanes", "Llanes", 15, 11), rankedResult("oviedo", "Oviedo", 8, 13)]
      : [rankedResult("salinas", "Salinas", 20, 14), rankedResult("gijon", "Gijón", 12, 15)];

  const forecasts = Object.fromEntries(["oviedo", "gijon", "llanes", "salinas"].map((key) => [key, {}]));
  const recommendations = buildDailyRecommendations(forecasts, "2026-08-06", ASTURIAS_LOCATIONS, { rankFn: fakeRank });

  assert.deepEqual(
    recommendations.map((r) => [r.activity_profile, r.location_key]),
    [
      ["beach_day", "salinas"],
      ["hiking", "llanes"],
    ],
  );
  // The window shown covers the whole block, inclusive of the final hour.
  assert.equal(recommendations[1].best_window, "11:00 - 14:00");
  assert.ok(recommendations.every((r) => r.is_good));
});

test("every configured location competes, including ones ranked below the cities", () => {
  const seen = [];
  const fakeRank = (forecasts) => {
    seen.push(Object.keys(forecasts).sort());
    return [rankedResult("cangas", "Cangas de Onís", 19, 9)];
  };
  const forecasts = Object.fromEntries(["oviedo", "gijon", "cangas"].map((key) => [key, {}]));

  const recommendations = buildDailyRecommendations(forecasts, "2026-08-06", ASTURIAS_LOCATIONS, { rankFn: fakeRank });

  assert.deepEqual(seen[0], ["cangas", "gijon", "oviedo"]);
  assert.ok(recommendations.every((r) => r.location_key === "cangas"));
});

test("a below-threshold best option is presented as no good opportunity", () => {
  const fakeRank = () => [rankedResult("oviedo", "Oviedo", 0, 12)];
  const recommendations = buildDailyRecommendations({ oviedo: {} }, "2026-08-06", ASTURIAS_LOCATIONS, { rankFn: fakeRank });

  const hiking = recommendations.find((r) => r.activity_profile === "hiking");
  assert.ok(hiking.normalized_score < GOOD_OPPORTUNITY_THRESHOLD);
  assert.equal(hiking.is_good, false);
  const line = formatRecommendationLine(hiking);
  assert.match(line, /no good option/);
  // The best available location and its score stay visible so the call can be judged.
  assert.match(line, /Oviedo/);
  assert.match(line, /12:00 - 15:00/);
  assert.match(line, /38\/100/);
});

test("a location with no usable window reports that rather than a fake score", () => {
  const recommendations = buildDailyRecommendations({ oviedo: {} }, "2026-08-06", ASTURIAS_LOCATIONS, { rankFn: () => [] });

  assert.ok(recommendations.every((r) => r.normalized_score === null));
  assert.equal(recommendations[0].score_text, "N/A");
  assert.match(formatRecommendationLine(recommendations[0]), /no usable window today/);
  assert.equal(recommendations[0].activity_profile, "beach_day");
});

test("notification lists one line per profile plus coverage", () => {
  const fakeRank = (forecasts, forecastDate, topN, activityProfile) =>
    activityProfile === ACTIVITY_HIKING
      ? [rankedResult("llanes", "Llanes", 18, 10)]
      : [rankedResult("salinas", "Salinas", 22, 13)];
  const recommendations = buildDailyRecommendations({ llanes: {}, salinas: {} }, "2026-08-06", ASTURIAS_LOCATIONS, {
    rankFn: fakeRank,
  });

  const content = buildOutlookNotification(recommendations, { loaded: 2, failed: 0 });
  assert.equal(content.body.split("\n").length, 2);
  assert.match(content.body, /Hiking: Llanes 10:00 - 13:00 \(90\/100\)/);
  assert.match(content.body, /Salinas 13:00 - 16:00 \(90\/100\)/);
  assert.equal(content.summaryText, "2 locations checked");
  assert.ok(content.largeBody.endsWith("2 locations checked"));
});

test("a total fetch failure is reported as an outage, not as bad weather", () => {
  const content = buildOutlookNotification([], { loaded: 0, failed: 4 });
  assert.equal(content.body, FORECAST_UNAVAILABLE_MESSAGE);
  assert.equal(content.summaryText, "No forecast data");
});

test("partial failures still recommend, and say how many locations were available", () => {
  const recommendations = buildDailyRecommendations({ llanes: {} }, "2026-08-06", ASTURIAS_LOCATIONS, {
    rankFn: () => [rankedResult("llanes", "Llanes", 18, 10)],
  });
  const content = buildOutlookNotification(recommendations, { loaded: 1, failed: 3 });

  assert.match(content.body, /Llanes/);
  assert.equal(content.summaryText, "1 of 4 locations available");
});
