import test from "node:test";
import assert from "node:assert/strict";
import { PRIORITY_LOCATIONS, buildNotificationContent, fetchTodaysNotificationContent } from "../js/background-task.js";

function row({ location_key, location_name, normalized_score, best_window = "11:00 - 14:00", is_priority = true, activity_label = "Beach" }) {
  return {
    location_key,
    location_name,
    normalized_score,
    best_window,
    is_priority,
    activity_label,
    score_text: normalized_score === null || normalized_score === undefined ? "N/A" : `${normalized_score}/100`,
  };
}

test("PRIORITY_LOCATIONS only includes oviedo and gijon", () => {
  assert.deepEqual(Object.keys(PRIORITY_LOCATIONS).sort(), ["gijon", "oviedo"]);
});

test("buildNotificationContent falls back when there are no rows", () => {
  const content = buildNotificationContent([]);
  assert.equal(content.body, "No good outdoor window found for today.");
  assert.equal(content.largeBody, null);
  assert.equal(content.summaryText, null);
});

test("buildNotificationContent highlights the best-scoring row and lists everything in largeBody", () => {
  const rows = [
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: 65, best_window: "09:00 - 12:00", activity_label: "Hiking" }),
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: 72, best_window: "14:00 - 17:00", activity_label: "Beach" }),
    row({ location_key: "gijon", location_name: "Gijón", normalized_score: 70, best_window: "10:00 - 13:00", activity_label: "Hiking" }),
    row({ location_key: "gijon", location_name: "Gijón", normalized_score: 80, best_window: "15:00 - 18:00", activity_label: "Beach" }),
    row({ location_key: "cangas", location_name: "Cangas de Onís", normalized_score: 89, best_window: "19:00 - 21:00", activity_label: "Hiking", is_priority: false }),
  ];
  const content = buildNotificationContent(rows);

  assert.equal(content.body, "🟢 Best: Hiking in Cangas de Onís, 19:00 - 21:00 (89/100)");
  assert.equal(
    content.largeBody,
    [
      "Oviedo\n  🟡 Hiking 09:00 - 12:00 (65/100)\n  🟡 Beach 14:00 - 17:00 (72/100)",
      "Gijón\n  🟡 Hiking 10:00 - 13:00 (70/100)\n  🟢 Beach 15:00 - 18:00 (80/100)",
      "Alt: Cangas de Onís\n  🟢 Hiking 19:00 - 21:00 (89/100)",
    ].join("\n\n"),
  );
  assert.equal(content.summaryText, "3 locations checked");
});

test("fetchTodaysNotificationContent falls back gracefully when the weather API is unreachable", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("network unavailable");
  };
  t.after(() => {
    globalThis.fetch = original;
  });

  const content = await fetchTodaysNotificationContent();
  assert.equal(content.body, "No good outdoor window found for today.");
});
