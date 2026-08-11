import test from "node:test";
import assert from "node:assert/strict";
import { PRIORITY_LOCATIONS, buildNotificationBody, fetchTodaysNotificationBody } from "../js/background-task.js";

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

test("buildNotificationBody falls back when there are no rows", () => {
  assert.equal(buildNotificationBody([]), "No good outdoor window found for today.");
});

test("buildNotificationBody groups priority cities and tags alternatives, without an em dash", () => {
  const rows = [
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: 65, best_window: "09:00 - 12:00", activity_label: "Hiking" }),
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: 72, best_window: "14:00 - 17:00", activity_label: "Beach" }),
    row({ location_key: "gijon", location_name: "Gijón", normalized_score: 70, best_window: "10:00 - 13:00", activity_label: "Hiking" }),
    row({ location_key: "gijon", location_name: "Gijón", normalized_score: 80, best_window: "15:00 - 18:00", activity_label: "Beach" }),
    row({ location_key: "cangas", location_name: "Cangas de Onís", normalized_score: 89, best_window: "19:00 - 21:00", activity_label: "Hiking", is_priority: false }),
  ];
  const body = buildNotificationBody(rows);
  assert.equal(
    body,
    [
      "Oviedo: Hiking 09:00 - 12:00 (65/100) · Beach 14:00 - 17:00 (72/100)",
      "Gijón: Hiking 10:00 - 13:00 (70/100) · Beach 15:00 - 18:00 (80/100)",
      "Alt (Cangas de Onís): Hiking 19:00 - 21:00 (89/100)",
    ].join("\n"),
  );
  assert.ok(!body.includes("—"));
});

test("fetchTodaysNotificationBody falls back gracefully when the weather API is unreachable", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("network unavailable");
  };
  t.after(() => {
    globalThis.fetch = original;
  });

  const body = await fetchTodaysNotificationBody();
  assert.equal(body, "No good outdoor window found for today.");
});
