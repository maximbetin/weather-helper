import test from "node:test";
import assert from "node:assert/strict";
import {
  FETCH_LEAD_MINUTES,
  LATE_WAKE_GRACE_MINUTES,
  fetchTodaysNotificationContent,
  planDailyRun,
} from "../js/background-task.js";
import { FORECAST_UNAVAILABLE_MESSAGE } from "../js/core/daily_summary.js";
import { madridDateKeyOf, madridInstantForDateKey } from "../js/core/timezone.js";
import { madridInstant } from "./helpers.js";

const REMINDER = "08:00";

test("a wake-up far ahead of the reminder does not fetch", () => {
  const now = madridInstant(2026, 8, 6, 3);
  const plan = planDailyRun(now, REMINDER, null);
  assert.equal(plan.action, "skip");
  assert.equal(plan.reason, "too-early");
});

test("a wake-up inside the lead window schedules for the reminder time itself", () => {
  const now = madridInstant(2026, 8, 6, 7);
  const plan = planDailyRun(now, REMINDER, null);

  assert.equal(plan.action, "schedule");
  assert.ok((plan.scheduleAt - now) / 60000 <= FETCH_LEAD_MINUTES);
  assert.deepEqual(plan.scheduleAt, madridInstant(2026, 8, 6, 8));
});

test("today's recommendation is never armed for tomorrow", () => {
  // A wake-up after the reminder time used to roll the alarm forward to the next
  // day, delivering today's forecast tomorrow morning.
  const now = madridInstant(2026, 8, 6, 9, 30);
  const plan = planDailyRun(now, REMINDER, null);

  assert.equal(plan.action, "schedule");
  assert.equal(plan.reason, "late-wake-up");
  assert.equal(madridDateKeyOf(plan.scheduleAt), "2026-08-06");
  assert.ok(plan.scheduleAt > now);
  assert.ok((plan.scheduleAt - now) / 60000 < 5);
});

test("a very late wake-up gives up rather than notifying at the wrong time of day", () => {
  const now = new Date(madridInstant(2026, 8, 6, 8).getTime() + (LATE_WAKE_GRACE_MINUTES + 30) * 60000);
  const plan = planDailyRun(now, REMINDER, null);
  assert.equal(plan.action, "skip");
  assert.equal(plan.reason, "too-late");
});

test("a date already processed is not notified twice", () => {
  const now = madridInstant(2026, 8, 6, 7, 30);
  const plan = planDailyRun(now, REMINDER, "2026-08-06");
  assert.equal(plan.action, "skip");
  assert.equal(plan.reason, "already-processed");

  const nextDay = planDailyRun(madridInstant(2026, 8, 7, 7, 30), REMINDER, "2026-08-06");
  assert.equal(nextDay.action, "schedule");
  assert.equal(nextDay.dateKey, "2026-08-07");
});

test("an unusable stored time falls back to the default reminder time", () => {
  const now = madridInstant(2026, 8, 6, 7, 30);
  const plan = planDailyRun(now, "not-a-time", null);
  assert.equal(plan.action, "schedule");
  assert.deepEqual(plan.scheduleAt, madridInstantForDateKey("2026-08-06", 8, 0));
});

test("fetchTodaysNotificationContent reports an outage when the weather API is unreachable", async (t) => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("network unavailable");
  };
  t.after(() => {
    globalThis.fetch = original;
  });

  const content = await fetchTodaysNotificationContent();
  assert.equal(content.body, FORECAST_UNAVAILABLE_MESSAGE);
});
