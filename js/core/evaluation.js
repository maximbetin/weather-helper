import { createDailyReport, createHourlyWeather } from "./models.js";
import { cloudScore, DEFAULT_ACTIVITY_PROFILE, getActivityScore, humidityScore, precipAmountScore, tempScore, windScore } from "./scoring.js";
import { addDaysToDateKey, madridDateKeyOf, madridHourOf, madridMinuteOf, nowInstant, parseForecastTimestamp } from "./timezone.js";

const DAYLIGHT_START_HOUR = 8;
const DAYLIGHT_END_HOUR = 20;
const FORECAST_DAYS = 7;

const ADJACENT_FORECAST_MINUTES_MIN = 50;
const ADJACENT_FORECAST_MINUTES_MAX = 70;
const CURRENT_HOUR_RELEVANCE_MINUTE = 30;
const DEFAULT_MAX_SCORE_VARIANCE = 7.0;
const OPTIMAL_MAX_SCORE_VARIANCE = 8.0;
const SINGLE_HOUR_MIN_AVG_SCORE = -1;
const MULTI_HOUR_MIN_AVG_SCORE = 0;
const VARIANCE_THRESHOLD_PER_EXTRA_HOUR = 0.8;
const MAX_DURATION_BONUS = 5.0;
const DURATION_BONUS_SATURATION_RATE = 0.35;
const CONSISTENCY_BONUS_WEIGHT = 2.0;
const WEAK_HOUR_PENALTY_WEIGHT = 0.2;
const DAY_SCORE_CHANGE_TOLERANCE = 4.0;
const DAY_SCORE_VOLATILITY_WEIGHT = 0.35;
const MAX_DAY_VOLATILITY_PENALTY = 10.0;
const OPPORTUNITY_TIE_TOLERANCE = 0.5;

function safeAverage(values) {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function averageHourAttribute(hours, attributeName) {
  const values = hours.map((hour) => hour[attributeName]).filter((value) => value !== null && value !== undefined);
  return safeAverage(values);
}

export function calculateWeatherAverages(hours) {
  return [
    averageHourAttribute(hours, "temp"),
    averageHourAttribute(hours, "wind"),
    averageHourAttribute(hours, "relative_humidity"),
    averageHourAttribute(hours, "precipitation_amount"),
  ];
}

function calculateBlockDetails(hours) {
  const clouds = hours.map((hour) => hour.cloud_coverage).filter((value) => value !== null && value !== undefined);
  const precipProbs = hours.map((hour) => hour.precipitation_probability).filter((value) => value !== null && value !== undefined);
  const symbols = [...new Set(hours.map((hour) => hour.symbol_code).filter(Boolean))].sort();
  return {
    cloud: safeAverage(clouds),
    precip_probability: safeAverage(precipProbs),
    symbols,
  };
}

export function areAdjacentForecastHours(previousHour, nextHour) {
  const deltaMinutes = (nextHour.time.getTime() - previousHour.time.getTime()) / 60000;
  return deltaMinutes >= ADJACENT_FORECAST_MINUTES_MIN && deltaMinutes <= ADJACENT_FORECAST_MINUTES_MAX;
}

function getPeriodData(entry, periodKey) {
  const period = (entry.data && entry.data[periodKey]) || {};
  return [period.summary || {}, period.details || {}];
}

export function isDaylightHour(hour) {
  return DAYLIGHT_START_HOUR <= hour.hour && hour.hour <= DAYLIGHT_END_HOUR;
}

function isFutureOrCurrentHour(hour, nowLocal) {
  const hourLocalHour = madridHourOf(hour.time);
  const nowLocalHour = madridHourOf(nowLocal);
  const nowLocalMinute = madridMinuteOf(nowLocal);
  return hour.time > nowLocal || (hourLocalHour === nowLocalHour && nowLocalMinute < CURRENT_HOUR_RELEVANCE_MINUTE);
}

export function filterHoursForRecommendations(hours, forecastDate, nowLocal) {
  const daylightHours = hours.filter(isDaylightHour);
  if (forecastDate !== madridDateKeyOf(nowLocal)) return daylightHours;
  return daylightHours.filter((hour) => isFutureOrCurrentHour(hour, nowLocal));
}

export function findOptimalWeatherBlock(hours, minDuration = 1, activityProfile = DEFAULT_ACTIVITY_PROFILE) {
  if (!hours || hours.length === 0) return null;
  const sortedHours = [...hours].sort((a, b) => a.time - b.time);
  const optimalBlock = findOptimalConsistentBlock(sortedHours, activityProfile, minDuration);
  return validMinimumDurationBlock(optimalBlock, minDuration);
}

function validMinimumDurationBlock(block, minDuration) {
  if (!block || block.duration < minDuration) return null;
  return block;
}

function extractHourlyWeatherValues(entry) {
  const instantDetails = entry.data.instant.details;
  const [precipitationAmount, precipitationProbability] = getPrecipitationValues(entry);
  return {
    time: parseForecastTimestamp(entry.time),
    temp: instantDetails.air_temperature ?? null,
    wind: instantDetails.wind_speed ?? null,
    cloud_coverage: instantDetails.cloud_area_fraction ?? null,
    precipitation_amount: precipitationAmount,
    precipitation_probability: precipitationProbability,
    symbol_code: getSymbolCode(entry),
    relative_humidity: instantDetails.relative_humidity ?? null,
  };
}

function getPrecipitationValues(entry) {
  const [, next1hDetails] = getPeriodData(entry, "next_1_hours");
  const [, next6hDetails] = getPeriodData(entry, "next_6_hours");
  return [
    firstAvailableDetail(next1hDetails, next6hDetails, "precipitation_amount"),
    firstAvailableDetail(next1hDetails, next6hDetails, "probability_of_precipitation"),
  ];
}

function firstAvailableDetail(primaryDetails, fallbackDetails, key) {
  const primaryValue = primaryDetails[key] ?? null;
  if (primaryValue !== null) return primaryValue;
  return fallbackDetails[key] ?? null;
}

function getSymbolCode(entry) {
  const [next1hSummary] = getPeriodData(entry, "next_1_hours");
  const [next6hSummary] = getPeriodData(entry, "next_6_hours");
  return next1hSummary.symbol_code || next6hSummary.symbol_code || null;
}

function buildHourlyWeather(values) {
  return createHourlyWeather({
    ...values,
    temp_score: tempScore(values.temp),
    wind_score: windScore(values.wind),
    cloud_score: cloudScore(values.cloud_coverage),
    precip_amount_score: precipAmountScore(values.precipitation_amount),
    humidity_score: humidityScore(values.relative_humidity),
  });
}

export function createHourlyWeatherFromEntry(entry) {
  return buildHourlyWeather(extractHourlyWeatherValues(entry));
}

function processTimeseries(forecastTimeseries) {
  const dailyForecasts = {};
  const today = madridDateKeyOf(nowInstant());
  const endDate = addDaysToDateKey(today, FORECAST_DAYS);
  for (const entry of forecastTimeseries) {
    appendForecastEntry(entry, dailyForecasts, today, endDate);
  }
  return dailyForecasts;
}

function appendForecastEntry(entry, dailyForecasts, today, endDate) {
  const forecastTime = parseForecastTimestamp(entry.time);
  const forecastDate = madridDateKeyOf(forecastTime);
  if (today <= forecastDate && forecastDate <= endDate) {
    if (!dailyForecasts[forecastDate]) dailyForecasts[forecastDate] = [];
    dailyForecasts[forecastDate].push(createHourlyWeatherFromEntry(entry));
  }
}

export function processForecast(forecastData, locationName) {
  const weatherData = forecastData && Object.prototype.hasOwnProperty.call(forecastData, "weather") ? forecastData.weather : forecastData;
  const forecastTimeseries = getForecastTimeseries(weatherData);
  if (forecastTimeseries === null) return null;
  const dailyForecasts = processTimeseries(forecastTimeseries);
  const dayScoresReports = buildDailyReports(dailyForecasts, locationName);
  return { daily_forecasts: dailyForecasts, day_scores: dayScoresReports };
}

function getForecastTimeseries(forecastData) {
  if (!forecastData || !("properties" in forecastData)) return null;
  return forecastData.properties.timeseries ?? null;
}

function buildDailyReports(dailyForecasts, locationName) {
  const dayScoresReports = {};
  for (const [forecastDate, hoursList] of Object.entries(dailyForecasts)) {
    const daylightHours = hoursList.filter(isDaylightHour);
    if (daylightHours.length > 0) {
      dayScoresReports[forecastDate] = createDailyReport(forecastDate, daylightHours, locationName);
    }
  }
  return dayScoresReports;
}

export function getAvailableDates(processedForecast) {
  if (!processedForecast || !("daily_forecasts" in processedForecast)) return [];
  return Object.keys(processedForecast.daily_forecasts).sort();
}

export function getTimeBlocksForDate(processedForecast, d) {
  if (!processedForecast || !("daily_forecasts" in processedForecast)) return [];
  const hours = processedForecast.daily_forecasts[d] || [];
  return [...hours].sort((a, b) => a.time - b.time);
}

function findConsistentBlocks(sortedHours, maxScoreVariance = DEFAULT_MAX_SCORE_VARIANCE, activityProfile = DEFAULT_ACTIVITY_PROFILE) {
  const blocks = [];
  for (const block of iterContiguousHourBlocks(sortedHours)) {
    const blockInfo = createConsistentBlockInfo(block, maxScoreVariance, activityProfile);
    if (blockInfo) blocks.push(blockInfo);
  }
  return blocks;
}

function iterContiguousHourBlocks(sortedHours) {
  const blocks = [];
  for (let startIdx = 0; startIdx < sortedHours.length; startIdx++) {
    blocks.push(...blocksFromStart(sortedHours, startIdx));
  }
  return blocks;
}

function blocksFromStart(sortedHours, startIdx) {
  const blocks = [];
  for (let endIdx = startIdx; endIdx < sortedHours.length; endIdx++) {
    if (hasForecastGap(sortedHours, startIdx, endIdx)) break;
    blocks.push(sortedHours.slice(startIdx, endIdx + 1));
  }
  return blocks;
}

function hasForecastGap(sortedHours, startIdx, endIdx) {
  return endIdx > startIdx && !areAdjacentForecastHours(sortedHours[endIdx - 1], sortedHours[endIdx]);
}

function createConsistentBlockInfo(block, maxScoreVariance, activityProfile) {
  const scores = block.map((hour) => getActivityScore(hour, activityProfile));
  const avgScore = scores.reduce((sum, value) => sum + value, 0) / scores.length;
  const stdDev = scoreStandardDeviation(scores, avgScore);
  if (!isAcceptableBlock(block, scores, avgScore, stdDev, maxScoreVariance)) return null;
  return buildBlockInfo(block, avgScore, stdDev, activityProfile);
}

function scoreStandardDeviation(scores, avgScore) {
  if (scores.length <= 1) return 0;
  const variance = scores.reduce((sum, score) => sum + (score - avgScore) ** 2, 0) / scores.length;
  return Math.sqrt(variance);
}

function isAcceptableBlock(block, scores, avgScore, stdDev, maxScoreVariance) {
  if (avgScore < minimumAverageScore(block.length)) return false;
  return stdDev <= adjustedVarianceThreshold(block.length, maxScoreVariance);
}

function minimumAverageScore(blockLength) {
  return blockLength === 1 ? SINGLE_HOUR_MIN_AVG_SCORE : MULTI_HOUR_MIN_AVG_SCORE;
}

function adjustedVarianceThreshold(blockLength, maxScoreVariance) {
  const extraHours = blockLength - 1;
  return maxScoreVariance + extraHours * VARIANCE_THRESHOLD_PER_EXTRA_HOUR;
}

function buildBlockInfo(block, avgScore, stdDev, activityProfile) {
  return {
    ...baseBlockInfo(block, avgScore, stdDev),
    ...weatherBlockInfo(block),
    ...calculateBlockDetails(block),
    activity_profile: activityProfile,
  };
}

function baseBlockInfo(block, avgScore, stdDev) {
  return {
    block,
    start: block[0].time,
    end: block[block.length - 1].time,
    avg_score: avgScore,
    duration: block.length,
    consistency: 1 / (1 + stdDev),
    variance: stdDev,
  };
}

function weatherBlockInfo(block) {
  const [avgTemp, avgWind, avgHumidity, avgPrecip] = calculateWeatherAverages(block);
  return { temp: avgTemp, wind: avgWind, humidity: avgHumidity, precip: avgPrecip };
}

function findOptimalConsistentBlock(sortedHours, activityProfile = DEFAULT_ACTIVITY_PROFILE, minDuration = 1) {
  const consistentBlocks = findConsistentBlocks(sortedHours, OPTIMAL_MAX_SCORE_VARIANCE, activityProfile);
  const candidates = blocksWithMinimumDuration(consistentBlocks, minDuration);
  const rankedBlocks = candidates.map((block) => rankBlock(block, activityProfile));
  if (rankedBlocks.length === 0) return null;
  return rankedBlocks.reduce((best, block) => (block.combined_score > best.combined_score ? block : best));
}

function blocksWithMinimumDuration(blocks, minDuration) {
  return blocks.filter((block) => block.duration >= minDuration);
}

function rankBlock(blockInfo, activityProfile) {
  const positiveHourCount = countPositiveHours(blockInfo, activityProfile);
  const durationBonus = durationBonusFor(positiveHourCount);
  const consistencyBonus = blockInfo.consistency * CONSISTENCY_BONUS_WEIGHT;
  const weakHourPenalty = weakHourPenaltyFor(blockInfo, activityProfile);
  const combinedScore = blockInfo.avg_score + durationBonus + consistencyBonus - weakHourPenalty;
  return blockWithRank(blockInfo, combinedScore, durationBonus, consistencyBonus, positiveHourCount);
}

function blockWithRank(blockInfo, combinedScore, durationBonus, consistencyBonus, positiveHourCount) {
  return {
    ...blockInfo,
    combined_score: combinedScore,
    duration_bonus: durationBonus,
    consistency_bonus: consistencyBonus,
    positive_hour_count: positiveHourCount,
  };
}

function durationBonusFor(positiveHourCount) {
  const extraHours = Math.max(0, positiveHourCount - 1);
  return MAX_DURATION_BONUS * (1 - Math.exp(-DURATION_BONUS_SATURATION_RATE * extraHours));
}

function countPositiveHours(blockInfo, activityProfile) {
  return blockInfo.block.filter((hour) => getActivityScore(hour, activityProfile) > 0).length;
}

function weakHourPenaltyFor(blockInfo, activityProfile) {
  const scores = blockInfo.block.map((hour) => getActivityScore(hour, activityProfile));
  const penalty = (blockInfo.avg_score - Math.min(...scores)) * WEAK_HOUR_PENALTY_WEIGHT;
  return Math.max(0, penalty);
}

export function getTopLocationsForDate(allLocationProcessed, d, topN = 10, activityProfile = DEFAULT_ACTIVITY_PROFILE) {
  const results = [];
  const nowLocal = nowInstant();
  for (const [locKey, processed] of Object.entries(allLocationProcessed)) {
    const locationResult = rankLocationForDate(locKey, processed, d, nowLocal, activityProfile);
    if (locationResult) results.push(locationResult);
  }
  results.sort(compareLocationResults);
  return results.slice(0, topN);
}

// Locations are ranked by the quality of their best usable continuous window
// (the optimal block's combined quality/duration/consistency score). The broader
// remaining-day score is only a tie-breaker for locations whose best opportunity
// is effectively as good as each other.
function compareLocationResults(a, b) {
  const opportunityDiff = b.opportunity_score - a.opportunity_score;
  if (Math.abs(opportunityDiff) > OPPORTUNITY_TIE_TOLERANCE) return opportunityDiff;
  return b.day_context_score - a.day_context_score;
}

function rankLocationForDate(locKey, processed, forecastDate, nowLocal, activityProfile) {
  const report = (processed.day_scores || {})[forecastDate];
  if (!report) return null;
  const filteredHours = locationRecommendationHours(processed, forecastDate, nowLocal);
  const optimalBlock = findOptimalConsistentBlock(filteredHours, activityProfile);
  if (!optimalBlock) return null;
  // Scored over the hours that are still ahead, so past hours never influence today.
  const dayScore = calculateDayActivityScore(filteredHours, activityProfile);
  return buildLocationResult(locKey, report, optimalBlock, dayScore, activityProfile);
}

function locationRecommendationHours(processed, forecastDate, nowLocal) {
  const dailyForecasts = processed.daily_forecasts || {};
  return filterHoursForRecommendations(dailyForecasts[forecastDate] || [], forecastDate, nowLocal);
}

function buildLocationResult(locKey, report, optimalBlock, dayScore, activityProfile) {
  return {
    location_key: locKey,
    location_name: report.location_name,
    // `score` ranks locations; `raw_score` is what gets shown next to the window,
    // so it is the window's own quality rather than any whole-day aggregate.
    score: optimalBlock.combined_score,
    opportunity_score: optimalBlock.combined_score,
    raw_score: optimalBlock.avg_score,
    window_score: optimalBlock.avg_score,
    day_context_score: dayScore.score,
    day_avg_score: dayScore.average,
    volatility_penalty: dayScore.volatility_penalty,
    optimal_block: optimalBlock,
    weather_desc: report.weather_description,
    activity_profile: activityProfile,
  };
}

export function calculateDayActivityScore(hours, activityProfile) {
  const sortedHours = [...hours].sort((a, b) => a.time - b.time);
  const scores = sortedHours.map((hour) => getActivityScore(hour, activityProfile));
  if (scores.length === 0) return { score: 0, average: 0, volatility_penalty: 0 };
  const average = scores.reduce((sum, value) => sum + value, 0) / scores.length;
  const volatilityPenalty = dayScoreVolatilityPenalty(sortedHours, scores);
  return { score: average - volatilityPenalty, average, volatility_penalty: volatilityPenalty };
}

function dayScoreVolatilityPenalty(sortedHours, scores) {
  const excessChanges = [];
  for (let index = 1; index < scores.length; index++) {
    if (areAdjacentForecastHours(sortedHours[index - 1], sortedHours[index])) {
      excessChanges.push(Math.max(0, Math.abs(scores[index] - scores[index - 1]) - DAY_SCORE_CHANGE_TOLERANCE));
    }
  }
  if (excessChanges.length === 0) return 0;
  const rootMeanSquare = Math.sqrt(excessChanges.reduce((sum, change) => sum + change ** 2, 0) / excessChanges.length);
  return Math.min(rootMeanSquare * DAY_SCORE_VOLATILITY_WEIGHT, MAX_DAY_VOLATILITY_PENALTY);
}
