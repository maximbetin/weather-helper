import test from "node:test";
import assert from "node:assert/strict";
import {
  FETCH_LEAD_MINUTES,
  LATE_WAKE_GRACE_MINUTES,
  applySettingsUpdate,
  fetchTodaysNotificationContent,
  planDailyRun,
  runDailyCheck,
  settingsChanged,
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

function installRunnerStubs(t, initial = {}) {
  const store = { ...initial };
  const scheduled = [];
  const previous = { kv: globalThis.CapacitorKV, notifications: globalThis.CapacitorNotifications };
  globalThis.CapacitorKV = {
    get: async (key) => ({ value: store[key] ?? "" }),
    set: async (key, value) => {
      store[key] = value;
    },
  };
  globalThis.CapacitorNotifications = { schedule: async (items) => scheduled.push(...items) };
  t.after(() => {
    globalThis.CapacitorKV = previous.kv;
    globalThis.CapacitorNotifications = previous.notifications;
  });
  return { store, scheduled };
}

test("re-pushing unchanged settings does not re-open an already-notified day", async (t) => {
  // initNotifications() pushes the stored settings on every app start; that must
  // not clear lastProcessedDate and allow a second notification for the same day.
  const { store } = installRunnerStubs(t, {
    notificationsEnabled: "true",
    notificationTime: "08:00",
    lastProcessedDate: "2026-08-06",
  });

  await applySettingsUpdate({ enabled: true, time: "08:00" });
  assert.equal(store.lastProcessedDate, "2026-08-06");

  assert.equal(settingsChanged({ enabled: true, time: "08:00" }, { enabled: true, time: "09:00" }), true);
  assert.equal(settingsChanged({ enabled: true, time: "08:00" }, { enabled: false, time: "08:00" }), true);
});

test("an actual settings change does clear the processed date", async (t) => {
  const { store } = installRunnerStubs(t, {
    notificationsEnabled: "true",
    notificationTime: "08:00",
    lastProcessedDate: "2026-08-06",
  });

  await applySettingsUpdate({ enabled: true, time: "10:00" });
  assert.equal(store.lastProcessedDate, "");
});

test("a complete forecast outage leaves the day unprocessed so a later wake-up retries", async (t) => {
  const { store, scheduled } = installRunnerStubs(t, {
    notificationsEnabled: "true",
    notificationTime: "08:00",
  });
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("network unavailable");
  };
  t.after(() => {
    globalThis.fetch = originalFetch;
  });

  await runDailyCheck(madridInstant(2026, 8, 6, 7, 30));
  assert.equal(scheduled.length, 1);
  assert.equal(scheduled[0].body, FORECAST_UNAVAILABLE_MESSAGE);
  // Not marked processed: the next hourly wake-up gets another chance.
  assert.ok(!store.lastProcessedDate);

  await runDailyCheck(madridInstant(2026, 8, 6, 8, 30));
  assert.equal(scheduled.length, 2);
});
