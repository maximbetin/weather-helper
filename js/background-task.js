import { fetchWeatherData } from "./core/weather_api.js";
import { processForecast } from "./core/evaluation.js";
import { buildDailySummary, formatOutlookNotificationBody, PRIORITY_LOCATION_KEYS } from "./core/daily_summary.js";
import { ASTURIAS_LOCATIONS } from "./core/locations.js";
import { madridDateKeyOf, nowInstant } from "./core/timezone.js";

export const DAILY_FORECAST_EVENT = "dailyForecastCheck";
const NOTIFICATION_ID = 1001;
const NOTIFICATION_TITLE = "Weather Helper";
const ALTERNATIVE_LIMIT = 1;

export const PRIORITY_LOCATIONS = Object.fromEntries(
  PRIORITY_LOCATION_KEYS.filter((key) => key in ASTURIAS_LOCATIONS).map((key) => [key, ASTURIAS_LOCATIONS[key]]),
);

export function buildNotificationBody(rows) {
  return formatOutlookNotificationBody(rows);
}

export async function fetchTodaysNotificationBody(locations = ASTURIAS_LOCATIONS) {
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
  return buildNotificationBody(rows);
}

function registerDailyForecastTask() {
  if (typeof addEventListener !== "function") return;
  addEventListener(DAILY_FORECAST_EVENT, async (resolve, reject) => {
    try {
      const body = await fetchTodaysNotificationBody();
      await CapacitorNotifications.schedule([{ id: NOTIFICATION_ID, title: NOTIFICATION_TITLE, body }]);
      resolve();
    } catch (error) {
      reject(error);
    }
  });
}

registerDailyForecastTask();
