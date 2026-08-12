export const TIMEZONE = "Europe/Madrid";

const partsFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function madridParts(instant) {
  const parts = {};
  for (const part of partsFormatter.formatToParts(instant)) {
    if (part.type !== "literal") parts[part.type] = part.value;
  }
  const hour = parts.hour === "24" ? 0 : Number(parts.hour);
  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour,
    minute: Number(parts.minute),
  };
}

export function madridHourOf(instant) {
  return madridParts(instant).hour;
}

export function madridMinuteOf(instant) {
  return madridParts(instant).minute;
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
function madridInstantForDateKey(dateKey, hour, minute) {
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

export function nextLocalOccurrence(hour, minute, from = new Date()) {
  const todayKey = madridDateKeyOf(from);
  const candidate = madridInstantForDateKey(todayKey, hour, minute);
  if (candidate.getTime() <= from.getTime()) {
    return madridInstantForDateKey(addDaysToDateKey(todayKey, 1), hour, minute);
  }
  return candidate;
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

export function formatDateKeyShort(dateKey) {
  const [year, month, day] = dateKey.split("-").map(Number);
  const utcNoon = new Date(Date.UTC(year, month - 1, day, 12));
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
  const parts = {};
  for (const part of formatter.formatToParts(utcNoon)) {
    if (part.type !== "literal") parts[part.type] = part.value;
  }
  return `${parts.weekday}, ${parts.day} ${parts.month}`;
}
