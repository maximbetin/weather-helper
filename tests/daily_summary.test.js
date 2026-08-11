import test from "node:test";
import assert from "node:assert/strict";
import { ASTURIAS_LOCATIONS } from "../js/core/locations.js";
import { buildDailySummary, formatDailySummary } from "../js/core/daily_summary.js";
import { ACTIVITY_HIKING } from "../js/core/scoring.js";
import { madridInstant } from "./helpers.js";

function rankedResult(locationKey, locationName, rawScore, startHour) {
  const start = madridInstant(2026, 8, 6, startHour);
  return {
    location_key: locationKey,
    location_name: locationName,
    raw_score: rawScore,
    optimal_block: { start, end: start },
  };
}

test("daily summary keeps priority cities first", () => {
  const fakeRank = (forecasts, forecastDate, topN, activityProfile) => {
    if (activityProfile === ACTIVITY_HIKING) {
      return [
        rankedResult("llanes", "Llanes", 22, 11),
        rankedResult("gijon", "Gijon", 18, 12),
        rankedResult("oviedo", "Oviedo", 8, 13),
      ];
    }
    return [
      rankedResult("salinas", "Salinas", 20, 14),
      rankedResult("gijon", "Gijon", 16, 15),
      rankedResult("oviedo", "Oviedo", 6, 16),
    ];
  };

  const forecasts = Object.fromEntries(["oviedo", "gijon", "llanes", "salinas"].map((key) => [key, {}]));

  const rows = buildDailySummary(forecasts, "2026-08-06", ASTURIAS_LOCATIONS, {
    alternativeLimit: 1,
    rankFn: fakeRank,
  });

  assert.deepEqual(
    rows.map((row) => [row.activity_profile, row.location_key]),
    [
      ["hiking", "oviedo"],
      ["hiking", "gijon"],
      ["beach_day", "oviedo"],
      ["beach_day", "gijon"],
      ["hiking", "llanes"],
      ["beach_day", "salinas"],
    ],
  );
  assert.ok(rows[0].score_text.endsWith("/100"));
  assert.equal(rows[0].best_window, "13:00 - 14:00");
  assert.ok(rows.slice(0, 4).every((row) => row.is_priority));
  assert.ok(!rows.slice(4).some((row) => row.is_priority));
});

test("daily summary keeps missing priority city visible", () => {
  const rows = buildDailySummary({ oviedo: {} }, "2026-08-06", ASTURIAS_LOCATIONS, {
    rankFn: () => [],
  });

  assert.deepEqual(
    rows.map((row) => [row.activity_profile, row.location_key]),
    [
      ["hiking", "oviedo"],
      ["beach_day", "oviedo"],
    ],
  );
  assert.equal(rows[0].score_text, "N/A");
  assert.equal(rows[0].best_window, "Not available");
});

test("daily summary text uses aligned columns without em dash", () => {
  const rows = buildDailySummary({ oviedo: {}, gijon: {} }, "2026-08-06", ASTURIAS_LOCATIONS);
  const text = formatDailySummary(rows, { forecastDate: "2026-08-06" });
  const tableLines = text
    .split("\n")
    .filter((line) => line && !line.startsWith("Daily ") && line !== "Alternatives");

  assert.ok(!text.includes("—"));
  assert.equal(tableLines[0].indexOf("Location"), tableLines[1].indexOf("Oviedo"));
  assert.equal(
    tableLines[0].indexOf("Score") + "Score".length,
    tableLines[1].indexOf(rows[0].score_text) + rows[0].score_text.length,
  );
  assert.ok(text.includes("Daily outdoor windows for Thu, 06 Aug"));
});
