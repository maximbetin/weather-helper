function isNumeric(value) {
  return typeof value === "number";
}

function normalizeRangeBounds(bounds) {
  const [low, high] = bounds;
  return [low === null ? -Infinity : low, high === null ? Infinity : high];
}

function valueInRange(value, bounds, inclusive) {
  const [low, high] = normalizeRangeBounds(bounds);
  return inclusive ? low <= value && value <= high : low <= value && value < high;
}

export function getValueFromRanges(value, ranges, inclusive = false) {
  if (value === null || value === undefined || !isNumeric(value)) return null;
  for (const [bounds, result] of ranges) {
    if (bounds === null) return result;
    if (valueInRange(value, bounds, inclusive)) return result;
  }
  return null;
}

function calculateScore(value, ranges, inclusive = false) {
  return getValueFromRanges(value, ranges, inclusive) ?? 0;
}

export const ACTIVITY_HIKING = "hiking";
export const ACTIVITY_BEACH_DAY = "beach_day";
export const DEFAULT_ACTIVITY_PROFILE = ACTIVITY_BEACH_DAY;
export const ACTIVITY_PROFILE_LABELS = {
  [ACTIVITY_HIKING]: "Hiking",
  [ACTIVITY_BEACH_DAY]: "Beach",
};

export const TEMP_RANGES = [
  [[20, 24], 7],
  [[17, 20], 6],
  [[24, 27], 6],
  [[15, 17], 4],
  [[27, 30], 4],
  [[10, 15], 2],
  [[30, 33], 1],
  [[5, 10], -1],
  [[33, 36], -3],
  [[0, 5], -6],
  [[36, 40], -9],
  [[-5, 0], -9],
  [null, -15],
];

export const WIND_RANGES = [
  [[1, 3], 2],
  [[0, 1], 1],
  [[3, 5], 0],
  [[5, 8], -2],
  [[8, 12], -4],
  [[12, 16], -6],
  [[16, 20], -7],
  [null, -8],
];

export const CLOUD_RANGES = [
  [[10, 30], 4],
  [[0, 10], 3],
  [[30, 60], 2],
  [[60, 80], 0],
  [[80, 95], -1],
  [null, -3],
];

export const PRECIP_AMOUNT_RANGES = [
  [[0, 0], 5],
  [[0, 0.1], 4],
  [[0.1, 0.5], 2],
  [[0.5, 1.0], 0],
  [[1.0, 2.5], -2],
  [[2.5, 5.0], -4],
  [[5.0, 10.0], -6],
  [[10.0, 20.0], -8],
  [null, -12],
];

export const HUMIDITY_RANGES = [
  [[40, 60], 3],
  [[30, 40], 2],
  [[60, 70], 1],
  [[20, 30], 0],
  [[70, 80], 0],
  [[80, 85], -1],
  [[15, 20], -1],
  [[85, 90], -2],
  [[10, 15], -2],
  [[90, 95], -3],
  [[5, 10], -3],
  [null, -4],
];

export const BEACH_TEMP_RANGES = [
  [[24, 30], 8],
  [[22, 24], 6],
  [[30, 32], 6],
  [[20, 22], 4],
  [[32, 34], 4],
  [[18, 20], 2],
  [[34, 36], 0],
  [[16, 18], -2],
  [[36, 39], -5],
  [[12, 16], -6],
  [null, -10],
];

export const BEACH_WIND_RANGES = [
  [[1, 4], 4],
  [[0, 1], 3],
  [[4, 6], 1],
  [[6, 8], -3],
  [[8, 11], -8],
  [[11, null], -14],
  [null, -14],
];

export const BEACH_CLOUD_RANGES = [
  [[0, 20], 6],
  [[20, 45], 4],
  [[45, 65], 1],
  [[65, 85], -2],
  [null, -5],
];

export const BEACH_PRECIP_AMOUNT_RANGES = [
  [[0, 0], 5],
  [[0, 0.1], 3],
  [[0.1, 0.5], -2],
  [[0.5, 1.0], -5],
  [[1.0, null], -10],
  [null, -10],
];

export const BEACH_HUMIDITY_RANGES = [
  [[45, 70], 3],
  [[35, 45], 2],
  [[70, 80], 0],
  [[25, 35], 0],
  [[80, 90], -2],
  [[0, 25], -3],
  [null, -4],
];

export const PRECIP_PROBABILITY_RANGES = [
  [[0, 15], 0],
  [[15, 35], -1],
  [[35, 55], -3],
  [[55, 75], -5],
  [null, -7],
];

export const BEACH_PRECIP_PROBABILITY_RANGES = [
  [[0, 10], 0],
  [[10, 25], -2],
  [[25, 40], -4],
  [[40, 60], -7],
  [null, -10],
];

export const SYMBOL_RISK_TERMS = [
  ["thunder", -12, -16, -20],
  ["snow", -8, -14, -14],
  ["sleet", -8, -14, -14],
  ["heavyrain", -7, -12, -8],
  ["rain", -5, -9, -4],
  ["showers", -4, -8, -2],
  ["fog", -3, -5, -6],
];

export const RATING_RANGES = [
  [[18.0, null], "Excellent"],
  [[13.0, 18.0], "Very Good"],
  [[7.0, 13.0], "Good"],
  [[2.0, 7.0], "Fair"],
  [null, "Poor"],
];

export const BEACH_RATING_RANGES = [
  [[22.0, null], "Excellent"],
  [[17.0, 22.0], "Very Good"],
  [[11.0, 17.0], "Good"],
  [[5.0, 11.0], "Fair"],
  [null, "Poor"],
];

export const RATING_RANGES_BY_PROFILE = {
  [ACTIVITY_HIKING]: RATING_RANGES,
  [ACTIVITY_BEACH_DAY]: BEACH_RATING_RANGES,
};

export const NORMALIZATION_CONFIG_BY_PROFILE = {
  [ACTIVITY_HIKING]: [18, 13, 7, 2, 23, 6],
  [ACTIVITY_BEACH_DAY]: [22, 17, 11, 5, 26, 5],
};

const NORMALIZED_POOR_THRESHOLD = 50;
const NORMALIZED_MIN_SCORE = 0;
const NORMALIZED_MAX_SCORE = 100;

export function tempScore(value) {
  return calculateScore(value, TEMP_RANGES, true);
}
export function windScore(value) {
  return calculateScore(value, WIND_RANGES, false);
}
export function cloudScore(value) {
  return calculateScore(value, CLOUD_RANGES, false);
}
export function precipAmountScore(value) {
  return calculateScore(value, PRECIP_AMOUNT_RANGES, true);
}
export function humidityScore(value) {
  return calculateScore(value, HUMIDITY_RANGES, true);
}
export function beachTempScore(value) {
  return calculateScore(value, BEACH_TEMP_RANGES, true);
}
export function beachWindScore(value) {
  return calculateScore(value, BEACH_WIND_RANGES, false);
}
export function beachCloudScore(value) {
  return calculateScore(value, BEACH_CLOUD_RANGES, false);
}
export function beachPrecipAmountScore(value) {
  return calculateScore(value, BEACH_PRECIP_AMOUNT_RANGES, true);
}
export function beachHumidityScore(value) {
  return calculateScore(value, BEACH_HUMIDITY_RANGES, true);
}
export function precipProbabilityScore(value) {
  return calculateScore(value, PRECIP_PROBABILITY_RANGES, true);
}
export function beachPrecipProbabilityScore(value) {
  return calculateScore(value, BEACH_PRECIP_PROBABILITY_RANGES, true);
}

export function symbolRiskScore(symbolCode, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  if (!symbolCode) return 0;
  const normalized = symbolCode.toLowerCase();
  for (const [term, hikingPenalty, beachPenalty] of SYMBOL_RISK_TERMS) {
    if (normalized.includes(term)) {
      return profileKey === ACTIVITY_BEACH_DAY ? beachPenalty : hikingPenalty;
    }
  }
  return 0;
}

export function beachDayScore(temp, windSpeed, cloudCoverage, precipitationAmount, relativeHumidity, precipitationProbability = null, symbolCode = null) {
  return (
    beachTempScore(temp) +
    beachWindScore(windSpeed) +
    beachCloudScore(cloudCoverage) +
    beachPrecipAmountScore(precipitationAmount) +
    beachHumidityScore(relativeHumidity) +
    beachPrecipProbabilityScore(precipitationProbability) +
    symbolRiskScore(symbolCode, ACTIVITY_BEACH_DAY)
  );
}

export function activityRiskScore(precipitationProbability, symbolCode, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  if (profileKey === ACTIVITY_BEACH_DAY) {
    return beachPrecipProbabilityScore(precipitationProbability) + symbolRiskScore(symbolCode, profileKey);
  }
  return precipProbabilityScore(precipitationProbability) + symbolRiskScore(symbolCode, profileKey);
}

export function getActivityProfileLabel(profileKey) {
  return ACTIVITY_PROFILE_LABELS[profileKey] ?? ACTIVITY_PROFILE_LABELS[DEFAULT_ACTIVITY_PROFILE];
}

export function getActivityProfileKey(label) {
  for (const [key, value] of Object.entries(ACTIVITY_PROFILE_LABELS)) {
    if (value === label) return key;
  }
  return DEFAULT_ACTIVITY_PROFILE;
}

const COMPONENT_RATING_RANGES = [
  [[4, null], "Excellent"],
  [[2, 4], "Very Good"],
  [[0, 2], "Good"],
  [[-3, 0], "Fair"],
  [null, "Poor"],
];

export function getComponentRating(score) {
  return getValueFromRanges(score, COMPONENT_RATING_RANGES, false) ?? "N/A";
}

export function getWeatherMetricRatings(hour, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  const beach = profileKey === ACTIVITY_BEACH_DAY;
  const scores = {
    temperature: beach ? beachTempScore(hour.temp) : (hour.temp_score ?? tempScore(hour.temp)),
    wind: beach ? beachWindScore(hour.wind) : (hour.wind_score ?? windScore(hour.wind)),
    clouds: beach ? beachCloudScore(hour.cloud_coverage) : (hour.cloud_score ?? cloudScore(hour.cloud_coverage)),
    precipitation: beach
      ? beachPrecipAmountScore(hour.precipitation_amount)
      : (hour.precip_amount_score ?? precipAmountScore(hour.precipitation_amount)),
    humidity: beach
      ? beachHumidityScore(hour.relative_humidity)
      : (hour.humidity_score ?? humidityScore(hour.relative_humidity)),
    precipitationProbability: beach
      ? beachPrecipProbabilityScore(hour.precipitation_probability)
      : precipProbabilityScore(hour.precipitation_probability),
  };
  return Object.fromEntries(Object.entries(scores).map(([key, score]) => [key, getComponentRating(score)]));
}

export function getActivityScore(hour, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  if (profileKey === ACTIVITY_BEACH_DAY) {
    return beachDayScore(
      hour.temp,
      hour.wind,
      hour.cloud_coverage,
      hour.precipitation_amount,
      hour.relative_humidity,
      hour.precipitation_probability ?? null,
      hour.symbol_code ?? null,
    );
  }
  return hour.total_score + activityRiskScore(hour.precipitation_probability ?? null, hour.symbol_code ?? null, profileKey);
}

export function getRatingInfo(score, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  if (score === null || score === undefined) return "N/A";
  const ranges = RATING_RANGES_BY_PROFILE[profileKey] ?? RATING_RANGES;
  return getValueFromRanges(score, ranges, false) ?? "N/A";
}

function getNormalizationConfig(profileKey) {
  return NORMALIZATION_CONFIG_BY_PROFILE[profileKey] ?? NORMALIZATION_CONFIG_BY_PROFILE[DEFAULT_ACTIVITY_PROFILE];
}

function scaleScore(score, lowerRaw, upperRaw, lowerNormalized, upperNormalized) {
  const span = upperNormalized - lowerNormalized;
  return lowerNormalized + (score - lowerRaw) * (span / (upperRaw - lowerRaw));
}

function calculateNormalizedScore(score, config) {
  const [excellent, veryGood, good, fair, maxExpected, poorSlope] = config;
  if (score >= excellent) return scaleScore(score, excellent, maxExpected, 90, 100);
  if (score >= veryGood) return scaleScore(score, veryGood, excellent, 80, 90);
  if (score >= good) return scaleScore(score, good, veryGood, 65, 80);
  if (score >= fair) return scaleScore(score, fair, good, 50, 65);
  return NORMALIZED_POOR_THRESHOLD + (score - fair) * poorSlope;
}

function roundHalfToEven(value) {
  const floorValue = Math.floor(value);
  const diff = value - floorValue;
  if (diff < 0.5) return floorValue;
  if (diff > 0.5) return floorValue + 1;
  return floorValue % 2 === 0 ? floorValue : floorValue + 1;
}

function clampNormalizedScore(normalized) {
  const rounded = roundHalfToEven(normalized);
  return Math.max(NORMALIZED_MIN_SCORE, Math.min(NORMALIZED_MAX_SCORE, rounded));
}

export function normalizeScore(score, profileKey = DEFAULT_ACTIVITY_PROFILE) {
  if (score === null || score === undefined) return 0;
  const config = getNormalizationConfig(profileKey);
  const normalized = calculateNormalizedScore(score, config);
  return clampNormalizedScore(normalized);
}
