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
