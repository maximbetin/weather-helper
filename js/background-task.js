import { fetchWeatherData } from "./core/weather_api.js";
import { processForecast } from "./core/evaluation.js";
import { buildDailySummary, buildOutlookNotification, PRIORITY_LOCATION_KEYS } from "./core/daily_summary.js";
import { ASTURIAS_LOCATIONS } from "./core/locations.js";
import { madridDateKeyOf, nowInstant, nextLocalOccurrence, DEFAULT_NOTIFICATION_TIME, parseTimeOfDay } from "./core/timezone.js";

export const DAILY_FORECAST_EVENT = "dailyForecastCheck";
export const UPDATE_SETTINGS_EVENT = "updateNotificationSettings";
const NOTIFICATION_ID = 1001;
const NOTIFICATION_TITLE = "Weather Helper";
const ALTERNATIVE_LIMIT = 1;
const KV_TIME_KEY = "notificationTime";
const KV_ENABLED_KEY = "notificationsEnabled";

export const PRIORITY_LOCATIONS = Object.fromEntries(
  PRIORITY_LOCATION_KEYS.filter((key) => key in ASTURIAS_LOCATIONS).map((key) => [key, ASTURIAS_LOCATIONS[key]]),
);

export function buildNotificationContent(rows) {
  return buildOutlookNotification(rows);
}

export async function fetchTodaysNotificationContent(locations = ASTURIAS_LOCATIONS) {
  const today = madridDateKeyOf(nowInstant());
  const forecasts = {};
  await Promise.all(
    Object.entries(locations).map(async ([key, location]) => {
      const data = await fetchWeatherData(location);
      const processed = data ? processForecast(data, location.name) : null;
      if (processed) forecasts[key] = processed;
    }),
  );
  const rows = buildDailySummary(forecasts, today, locations, { alternativeLimit: ALTERNATIVE_LIMIT });
  return buildNotificationContent(rows);
}

async function readSettings() {
  const enabledEntry = await CapacitorKV.get(KV_ENABLED_KEY);
  const timeEntry = await CapacitorKV.get(KV_TIME_KEY);
  const enabled = enabledEntry?.value === "true";
  const parsed = parseTimeOfDay(timeEntry?.value);
  const time = parsed ? timeEntry.value : DEFAULT_NOTIFICATION_TIME;
  return { enabled, time };
}

async function scheduleTodaysNotification(time) {
  const parsed = parseTimeOfDay(time) ?? parseTimeOfDay(DEFAULT_NOTIFICATION_TIME);
  const { body, largeBody, summaryText } = await fetchTodaysNotificationContent();
  const scheduleAt = nextLocalOccurrence(parsed.hour, parsed.minute);
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
}

function registerDailyForecastTask() {
  if (typeof addEventListener !== "function") return;

  addEventListener(DAILY_FORECAST_EVENT, async (resolve, reject) => {
    try {
      const { enabled, time } = await readSettings();
      if (enabled) await scheduleTodaysNotification(time);
      resolve();
    } catch (error) {
      reject(error);
    }
  });

  addEventListener(UPDATE_SETTINGS_EVENT, async (resolve, reject, args) => {
    try {
      const details = args ?? {};
      const enabled = Boolean(details.enabled);
      const time = parseTimeOfDay(details.time) ? details.time : DEFAULT_NOTIFICATION_TIME;
      await CapacitorKV.set(KV_ENABLED_KEY, String(enabled));
      await CapacitorKV.set(KV_TIME_KEY, time);
      if (enabled) await scheduleTodaysNotification(time);
      resolve();
    } catch (error) {
      reject(error);
    }
  });
}

registerDailyForecastTask();
