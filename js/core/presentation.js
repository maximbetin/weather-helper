import { formatMadridTime, formatDateKeyShort } from "./timezone.js";

export const BASE_COLORS = {
  primary: "#1e3a8a",
  background: "#f8fafc",
  surface: "#ffffff",
  border: "#e2e8f0",
  text: "#1e293b",
  text_secondary: "#64748b",
  excellent: "#15803d",
  very_good: "#65a30d",
  good: "#ca8a04",
  fair: "#ea580c",
  poor: "#b91c1c",
};

export const RATING_COLORS = {
  Excellent: BASE_COLORS.excellent,
  "Very Good": BASE_COLORS.very_good,
  Good: BASE_COLORS.good,
  Fair: BASE_COLORS.fair,
  Poor: BASE_COLORS.poor,
};

export const RATING_BACKGROUNDS = {
  Excellent: "#f0fdf4",
  "Very Good": "#f7fee7",
  Good: "#fefce8",
  Fair: "#fff7ed",
  Poor: "#fef2f2",
};

export function getRatingColor(rating) {
  return RATING_COLORS[rating] ?? BASE_COLORS.text;
}

export function getRatingBackground(rating) {
  return RATING_BACKGROUNDS[rating] ?? BASE_COLORS.surface;
}

export function formatTemperature(value, unit = "°C") {
  return value === null || value === undefined ? "N/A" : `${value.toFixed(1)}${unit}`;
}

export function formatPercentage(value, suffix = "%") {
  return value === null || value === undefined ? "N/A" : `${value.toFixed(0)}${suffix}`;
}

export function formatPrecipitation(value, unit = " mm") {
  return value === null || value === undefined ? "N/A" : `${value.toFixed(1)}${unit}`;
}

export function formatWindSpeed(value) {
  return value === null || value === undefined ? "N/A" : `${(value * 3.6).toFixed(1)} km/h`;
}

export function formatDuration(hours) {
  return hours === 1 ? "1 hour" : `${hours} hours`;
}

export const formatTime = formatMadridTime;

export function formatDate(dateKey) {
  return formatDateKeyShort(dateKey);
}
