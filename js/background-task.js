import { fetchWeatherData } from "./core/weather_api.js";
import { processForecast } from "./core/evaluation.js";
import { buildDailySummary, PRIORITY_LOCATION_KEYS } from "./core/daily_summary.js";
import { ASTURIAS_LOCATIONS } from "./core/locations.js";
import { madridDateKeyOf, nowInstant } from "./core/timezone.js";

export const DAILY_FORECAST_EVENT = "dailyForecastCheck";
const NOTIFICATION_ID = 1001;
const NOTIFICATION_TITLE = "Weather Helper";
const NO_WINDOW_BODY = "No good outdoor window found for today.";

export const PRIORITY_LOCATIONS = Object.fromEntries(
  PRIORITY_LOCATION_KEYS.filter((key) => key in ASTURIAS_LOCATIONS).map((key) => [key, ASTURIAS_LOCATIONS[key]]),
);

export function pickBestPriorityRow(rows) {
  const candidates = rows.filter(
    (row) => row.is_priority && row.normalized_score !== null && row.normalized_score !== undefined,
  );
  if (candidates.length === 0) return null;
  return candidates.reduce((best, row) => (row.normalized_score > best.normalized_score ? row : best));
}

export function buildNotificationBody(rows) {
  const best = pickBestPriorityRow(rows);
  if (!best) return NO_WINDOW_BODY;
  return `${best.activity_label} ${best.score_text} · ${best.location_name} · ${best.best_window} - today's best window.`;
}

export async function fetchTodaysNotificationBody(locations = PRIORITY_LOCATIONS) {
  const today = madridDateKeyOf(nowInstant());
  const forecasts = {};
  for (const [key, location] of Object.entries(locations)) {
    const data = await fetchWeatherData(location);
    const processed = data ? processForecast(data, location.name) : null;
    if (processed) forecasts[key] = processed;
  }
  const rows = buildDailySummary(forecasts, today, locations);
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
