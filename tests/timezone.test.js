import test from "node:test";
import assert from "node:assert/strict";
import { nextLocalOccurrence, madridHourOf, madridMinuteOf } from "../js/core/timezone.js";

test("nextLocalOccurrence resolves to the Madrid wall clock, not the process's local timezone", () => {
  // 2026-01-15T10:00:00Z is 11:00 in Madrid (CET, UTC+1) during winter.
  const from = new Date("2026-01-15T10:00:00Z");
  const result = nextLocalOccurrence(8, 0, from);
  assert.equal(madridHourOf(result), 8);
  assert.equal(madridMinuteOf(result), 0);
  // The target time already passed today in Madrid, so it should roll to tomorrow.
  assert.equal(result.toISOString(), "2026-01-16T07:00:00.000Z");
});

test("nextLocalOccurrence stays on the same Madrid day when the time hasn't passed yet", () => {
  const from = new Date("2026-01-15T06:00:00Z"); // 07:00 Madrid
  const result = nextLocalOccurrence(8, 0, from);
  assert.equal(result.toISOString(), "2026-01-15T07:00:00.000Z");
});

test("nextLocalOccurrence accounts for the CET/CEST offset change", () => {
  // 2026-07-15 is CEST (UTC+2) in Madrid.
  const from = new Date("2026-07-15T05:00:00Z");
  const result = nextLocalOccurrence(8, 0, from);
  assert.equal(result.toISOString(), "2026-07-15T06:00:00.000Z");
});
