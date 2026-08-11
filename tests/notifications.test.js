import test from "node:test";
import assert from "node:assert/strict";
import { parseTime, buildDailyScheduleOptions, DEFAULT_NOTIFICATION_TIME } from "../js/notifications.js";

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

test("buildDailyScheduleOptions builds a repeating daily schedule", () => {
  const options = buildDailyScheduleOptions(DEFAULT_NOTIFICATION_TIME);
  assert.equal(options.notifications.length, 1);

  const [notification] = options.notifications;
  assert.equal(notification.id, 1001);
  assert.equal(notification.title, "Weather Helper");
  assert.equal(typeof notification.body, "string");
  assert.equal(notification.schedule.repeats, true);
  assert.equal(notification.schedule.every, "day");
  assert.equal(notification.schedule.allowWhileIdle, true);
  assert.ok(notification.schedule.at instanceof Date);
  assert.equal(notification.schedule.at.getHours(), 8);
  assert.equal(notification.schedule.at.getMinutes(), 0);
});

test("buildDailyScheduleOptions honors the requested time", () => {
  const options = buildDailyScheduleOptions("14:30");
  const { at } = options.notifications[0].schedule;
  assert.equal(at.getHours(), 14);
  assert.equal(at.getMinutes(), 30);
});

test("buildDailyScheduleOptions rejects invalid time", () => {
  assert.throws(() => buildDailyScheduleOptions("invalid"));
});
