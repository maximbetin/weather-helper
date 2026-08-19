import test from "node:test";
import assert from "node:assert/strict";
import { madridInstantForDateKey, madridHourOf, madridMinuteOf } from "../js/core/timezone.js";

test("madridInstantForDateKey resolves to the Madrid wall clock, not the process's local timezone", () => {
  const result = madridInstantForDateKey("2026-01-15", 8, 0);
  assert.equal(madridHourOf(result), 8);
  assert.equal(madridMinuteOf(result), 0);
  // Winter: Madrid is CET (UTC+1).
  assert.equal(result.toISOString(), "2026-01-15T07:00:00.000Z");
});

test("madridInstantForDateKey stays on the requested day rather than rolling forward", () => {
  const result = madridInstantForDateKey("2026-01-15", 6, 30);
  assert.equal(result.toISOString(), "2026-01-15T05:30:00.000Z");
});

test("madridInstantForDateKey accounts for the CET/CEST offset change", () => {
  // 2026-07-15 is CEST (UTC+2) in Madrid.
  const result = madridInstantForDateKey("2026-07-15", 8, 0);
  assert.equal(result.toISOString(), "2026-07-15T06:00:00.000Z");
});
