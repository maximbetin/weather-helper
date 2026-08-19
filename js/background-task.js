import { fetchWeatherData } from "./core/weather_api.js";
import { processForecast } from "./core/evaluation.js";
import { buildDailyRecommendations, buildOutlookNotification } from "./core/daily_summary.js";
import { ASTURIAS_LOCATIONS } from "./core/locations.js";
import { madridDateKeyOf, madridInstantForDateKey, nowInstant, DEFAULT_NOTIFICATION_TIME, parseTimeOfDay } from "./core/timezone.js";

export const DAILY_FORECAST_EVENT = "dailyForecastCheck";
export const UPDATE_SETTINGS_EVENT = "updateNotificationSettings";
const NOTIFICATION_ID = 1001;
const NOTIFICATION_TITLE = "Weather Helper";
const KV_TIME_KEY = "notificationTime";
const KV_ENABLED_KEY = "notificationsEnabled";
const KV_PROCESSED_DATE_KEY = "lastProcessedDate";

// The runner wakes up roughly hourly, but a forecast is only fetched inside a
// window around the reminder time, so the notification content is fresh without
// hitting MET Norway twelve times a day.
export const FETCH_LEAD_MINUTES = 90;
// If the OS wakes the runner late (Doze, battery optimisation), still deliver
// today's recommendation rather than skipping the day entirely.
export const LATE_WAKE_GRACE_MINUTES = 120;
const LATE_DELIVERY_DELAY_MS = 60 * 1000;

// Decides, without any I/O, whether this wake-up should fetch and schedule.
// Because the schedule instant is always derived from *today's* date key, a
// recommendation computed today can never be armed as tomorrow's notification.
export function planDailyRun(now, time, lastProcessedDate) {
  const parsed = parseTimeOfDay(time) ?? parseTimeOfDay(DEFAULT_NOTIFICATION_TIME);
  const dateKey = madridDateKeyOf(now);
  if (lastProcessedDate === dateKey) return { action: "skip", reason: "already-processed", dateKey, scheduleAt: null };

  const reminderAt = madridInstantForDateKey(dateKey, parsed.hour, parsed.minute);
  const minutesUntilReminder = (reminderAt.getTime() - now.getTime()) / 60000;
  if (minutesUntilReminder > FETCH_LEAD_MINUTES) return { action: "skip", reason: "too-early", dateKey, scheduleAt: null };
  if (minutesUntilReminder < -LATE_WAKE_GRACE_MINUTES) return { action: "skip", reason: "too-late", dateKey, scheduleAt: null };

  if (minutesUntilReminder > 0) return { action: "schedule", reason: "ahead-of-reminder", dateKey, scheduleAt: reminderAt };
  return { action: "schedule", reason: "late-wake-up", dateKey, scheduleAt: new Date(now.getTime() + LATE_DELIVERY_DELAY_MS) };
}

async function loadForecasts(locations) {
  const forecasts = {};
  let failed = 0;
  await Promise.all(
    Object.entries(locations).map(async ([key, location]) => {
      try {
        const data = await fetchWeatherData(location);
        const processed = data ? processForecast(data, location.name) : null;
        if (processed) forecasts[key] = processed;
        else failed += 1;
      } catch (error) {
        console.error(`Background forecast fetch failed for ${key}: ${error}`);
        failed += 1;
      }
    }),
  );
  return { forecasts, failed };
}

export async function fetchTodaysNotificationContent(locations = ASTURIAS_LOCATIONS) {
  const today = madridDateKeyOf(nowInstant());
  const { forecasts, failed } = await loadForecasts(locations);
  const loaded = Object.keys(forecasts).length;
  // No location loaded at all is an outage, not bad weather — say so rather than
  // reporting "no good window".
  if (loaded === 0) return { ...buildOutlookNotification([], { loaded: 0, failed }), loaded, failed };
  const recommendations = buildDailyRecommendations(forecasts, today, locations);
  return { ...buildOutlookNotification(recommendations, { loaded, failed }), loaded, failed };
}

async function readSettings() {
  const enabledEntry = await CapacitorKV.get(KV_ENABLED_KEY);
  const timeEntry = await CapacitorKV.get(KV_TIME_KEY);
  const processedEntry = await CapacitorKV.get(KV_PROCESSED_DATE_KEY);
  const enabled = enabledEntry?.value === "true";
  const parsed = parseTimeOfDay(timeEntry?.value);
  const time = parsed ? timeEntry.value : DEFAULT_NOTIFICATION_TIME;
  return { enabled, time, lastProcessedDate: processedEntry?.value ?? null };
}

// Returns false when not a single location could be fetched, so the caller can
// leave the day unprocessed and retry on a later wake-up.
async function scheduleTodaysNotification(scheduleAt) {
  const { body, largeBody, summaryText, loaded } = await fetchTodaysNotificationContent();
  await CapacitorNotifications.schedule([
    {
      id: NOTIFICATION_ID,
      title: NOTIFICATION_TITLE,
      body,
      largeBody: largeBody ?? undefined,
      summaryText: summaryText ?? undefined,
      scheduleAt,
    },
  ]);
  return loaded > 0;
}

export async function runDailyCheck(now = nowInstant()) {
  const { enabled, time, lastProcessedDate } = await readSettings();
  if (!enabled) return;
  const plan = planDailyRun(now, time, lastProcessedDate);
  if (plan.action !== "schedule") return;
  const hadForecast = await scheduleTodaysNotification(plan.scheduleAt);
  // Marked only after a successful schedule with real forecast data, so a failed
  // run (or a complete outage) retries on the next hourly wake-up.
  if (hadForecast) await CapacitorKV.set(KV_PROCESSED_DATE_KEY, plan.dateKey);
}

// Opening the app re-pushes the stored settings unchanged; only a real change to
// enabled/time may clear the processed date and allow a second same-day notification.
export function settingsChanged(stored, incoming) {
  return stored.enabled !== incoming.enabled || stored.time !== incoming.time;
}

export async function applySettingsUpdate(details = {}) {
  const enabled = Boolean(details.enabled);
  const time = parseTimeOfDay(details.time) ? details.time : DEFAULT_NOTIFICATION_TIME;
  const stored = await readSettings();
  const changed = settingsChanged({ enabled: stored.enabled, time: stored.time }, { enabled, time });
  await CapacitorKV.set(KV_ENABLED_KEY, String(enabled));
  await CapacitorKV.set(KV_TIME_KEY, time);
  // A settings change invalidates whatever was already armed for today.
  if (changed) await CapacitorKV.set(KV_PROCESSED_DATE_KEY, "");
  if (enabled) await runDailyCheck();
}

function registerDailyForecastTask() {
  if (typeof addEventListener !== "function") return;

  addEventListener(DAILY_FORECAST_EVENT, async (resolve, reject) => {
    try {
      await runDailyCheck();
      resolve();
    } catch (error) {
      reject(error);
    }
  });

  addEventListener(UPDATE_SETTINGS_EVENT, async (resolve, reject, args) => {
    try {
      await applySettingsUpdate(args ?? {});
      resolve();
    } catch (error) {
      reject(error);
    }
  });
}

registerDailyForecastTask();
