import test from "node:test";
import assert from "node:assert/strict";
import { parseTime } from "../js/notifications.js";

test("parseTime accepts valid HH:MM values", () => {
  assert.deepEqual(parseTime("00:00"), { hour: 0, minute: 0 });
  assert.deepEqual(parseTime("08:00"), { hour: 8, minute: 0 });
  assert.deepEqual(parseTime("23:59"), { hour: 23, minute: 59 });
  assert.deepEqual(parseTime("09:45"), { hour: 9, minute: 45 });
});

test("parseTime rejects invalid values", () => {
  assert.equal(parseTime("24:00"), null);
  assert.equal(parseTime("12:60"), null);
  assert.equal(parseTime("8:00"), null);
  assert.equal(parseTime(""), null);
  assert.equal(parseTime(null), null);
  assert.equal(parseTime(undefined), null);
  assert.equal(parseTime("not-a-time"), null);
});
