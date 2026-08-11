import test from "node:test";
import assert from "node:assert/strict";
import {
  PRIORITY_LOCATIONS,
  pickBestPriorityRow,
  buildNotificationBody,
  fetchTodaysNotificationBody,
} from "../js/background-task.js";

function row({ location_key, location_name, normalized_score, best_window = "11:00 - 14:00", is_priority = true, activity_label = "Beach" }) {
  return { location_key, location_name, normalized_score, best_window, is_priority, activity_label, score_text: `${normalized_score}/100` };
}

test("PRIORITY_LOCATIONS only includes oviedo and gijon", () => {
  assert.deepEqual(Object.keys(PRIORITY_LOCATIONS).sort(), ["gijon", "oviedo"]);
});

test("pickBestPriorityRow returns null when no priority row has a score", () => {
  const rows = [
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: null }),
    row({ location_key: "llanes", location_name: "Llanes", normalized_score: 90, is_priority: false }),
  ];
  assert.equal(pickBestPriorityRow(rows), null);
});

test("pickBestPriorityRow picks the highest-scoring priority row", () => {
  const rows = [
    row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: 40 }),
    row({ location_key: "gijon", location_name: "Gijón", normalized_score: 82 }),
    row({ location_key: "llanes", location_name: "Llanes", normalized_score: 95, is_priority: false }),
  ];
  assert.equal(pickBestPriorityRow(rows).location_key, "gijon");
});

test("buildNotificationBody falls back when no priority window is available", () => {
  const rows = [row({ location_key: "oviedo", location_name: "Oviedo", normalized_score: null })];
  assert.equal(buildNotificationBody(rows), "No good outdoor window found for today.");
});

test("buildNotificationBody formats the best priority row without an em dash", () => {
  const rows = [row({ location_key: "gijon", location_name: "Gijón", normalized_score: 82, best_window: "11:00 - 14:00" })];
  const body = buildNotificationBody(rows);
  assert.equal(body, "Beach 82/100 · Gijón · 11:00 - 14:00 - today's best window.");
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
