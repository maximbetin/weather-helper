import { createHourlyWeather } from "../js/core/models.js";

const partsFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Madrid",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function madridPartsAsUTC(instant) {
  const parts = {};
  for (const part of partsFormatter.formatToParts(instant)) {
    if (part.type !== "literal") parts[part.type] = part.value;
  }
  const hour = parts.hour === "24" ? 0 : Number(parts.hour);
  return Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), hour, Number(parts.minute));
}

// Builds the absolute instant whose Europe/Madrid wall-clock reads the given
// year/month/day/hour/minute, regardless of CET/CEST. Mirrors how the Python
// tests used naive local datetimes directly as Madrid wall-clock time.
export function madridInstant(year, month, day, hour, minute = 0) {
  let guess = new Date(Date.UTC(year, month - 1, day, hour, minute));
  for (let i = 0; i < 3; i++) {
    const wantUTCEquivalent = Date.UTC(year, month - 1, day, hour, minute);
    const gotUTCEquivalent = madridPartsAsUTC(guess);
    const diff = wantUTCEquivalent - gotUTCEquivalent;
    if (diff === 0) break;
    guess = new Date(guess.getTime() + diff);
  }
  return guess;
}

// Port of the Python `create_hour` conftest fixture.
export function createHour(time, totalScore = null, overrides = {}) {
  const defaults = {
    temp: 20,
    wind: 1,
    precipitation_amount: 0.0,
    relative_humidity: 60,
    cloud_coverage: 20,
    temp_score: 0,
    wind_score: 0,
    cloud_score: 0,
    precip_amount_score: 0,
    humidity_score: 0,
  };
  if (totalScore !== null) {
    const base = Math.floor(totalScore / 4);
    const remainder = totalScore - 3 * base;
    Object.assign(defaults, { temp_score: base, wind_score: base, cloud_score: base, precip_amount_score: remainder });
  }
  Object.assign(defaults, overrides);
  return createHourlyWeather({ time, ...defaults });
}
