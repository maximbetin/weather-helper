export const TIMEZONE = "Europe/Madrid";
export const DEFAULT_NOTIFICATION_TIME = "08:00";

export function parseTimeOfDay(value) {
  const match = /^([0-1]\d|2[0-3]):([0-5]\d)$/.exec(value ?? "");
  if (!match) return null;
  return { hour: Number(match[1]), minute: Number(match[2]) };
}

// The background-runner's embedded JS engine has no `Intl` global at all (it's a
// minimal engine without ICU data), so Madrid's wall-clock time is computed here via
// the EU DST rule directly instead of Intl.DateTimeFormat - this file must work
// identically in both the WebView (full Intl) and that headless engine (none).
// EU DST: clocks go forward at 01:00 UTC on the last Sunday of March (UTC+1 -> UTC+2)
// and back at 01:00 UTC on the last Sunday of October (UTC+2 -> UTC+1).
function lastSundayUTC(year, monthIndex, hourUTC) {
  const lastDayOfMonth = new Date(Date.UTC(year, monthIndex + 1, 0, hourUTC));
  lastDayOfMonth.setUTCDate(lastDayOfMonth.getUTCDate() - lastDayOfMonth.getUTCDay());
  return lastDayOfMonth;
}

function madridOffsetMinutes(instant) {
  const year = instant.getUTCFullYear();
  const dstStart = lastSundayUTC(year, 2, 1);
  const dstEnd = lastSundayUTC(year, 9, 1);
  return instant >= dstStart && instant < dstEnd ? 120 : 60;
}

function madridParts(instant) {
  const local = new Date(instant.getTime() + madridOffsetMinutes(instant) * 60000);
  return {
    year: local.getUTCFullYear(),
    month: local.getUTCMonth() + 1,
    day: local.getUTCDate(),
    hour: local.getUTCHours(),
    minute: local.getUTCMinutes(),
  };
}

export function madridHourOf(instant) {
  return madridParts(instant).hour;
}

export function madridMinuteOf(instant) {
  return madridParts(instant).minute;
}

export function formatMadridTime(instant) {
  const hour = String(madridHourOf(instant)).padStart(2, "0");
  const minute = String(madridMinuteOf(instant)).padStart(2, "0");
  return `${hour}:${minute}`;
}

export function madridDateKeyOf(instant) {
  const { year, month, day } = madridParts(instant);
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function nowInstant() {
  return new Date();
}

function madridWallClockAsUTCMillis(instant) {
  const { year, month, day, hour, minute } = madridParts(instant);
  return Date.UTC(year, month - 1, day, hour, minute);
}

// Finds the absolute instant whose Europe/Madrid wall-clock reads
// dateKey@hour:minute, regardless of the executing environment's own
// timezone (the background task's JS engine may not agree with the
// device's Android timezone, so this can't rely on Date's local setters).
export function madridInstantForDateKey(dateKey, hour, minute) {
  const [year, month, day] = dateKey.split("-").map(Number);
  const want = Date.UTC(year, month - 1, day, hour, minute);
  let guess = new Date(want);
  for (let i = 0; i < 3; i++) {
    const diff = want - madridWallClockAsUTCMillis(guess);
    if (diff === 0) break;
    guess = new Date(guess.getTime() + diff);
  }
  return guess;
}

export function parseForecastTimestamp(timestamp) {
  return new Date(timestamp);
}

export function addDaysToDateKey(dateKey, days) {
  const [year, month, day] = dateKey.split("-").map(Number);
  const utcNoon = Date.UTC(year, month - 1, day, 12);
  const shifted = new Date(utcNoon + days * 24 * 60 * 60 * 1000);
  return `${String(shifted.getUTCFullYear()).padStart(4, "0")}-${String(shifted.getUTCMonth() + 1).padStart(2, "0")}-${String(shifted.getUTCDate()).padStart(2, "0")}`;
}

const WEEKDAY_NAMES_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_NAMES_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatDateKeyShort(dateKey) {
  const [year, month, day] = dateKey.split("-").map(Number);
  const utcNoon = new Date(Date.UTC(year, month - 1, day, 12));
  const weekday = WEEKDAY_NAMES_SHORT[utcNoon.getUTCDay()];
  const monthName = MONTH_NAMES_SHORT[utcNoon.getUTCMonth()];
  return `${weekday}, ${String(day).padStart(2, "0")} ${monthName}`;
}
