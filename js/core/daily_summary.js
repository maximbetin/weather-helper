import { getTopLocationsForDate } from "./evaluation.js";
import { ACTIVITY_BEACH_DAY, ACTIVITY_HIKING, getActivityProfileLabel, normalizeScore } from "./scoring.js";
import { formatMadridTime } from "./timezone.js";

export const SUMMARY_ACTIVITY_PROFILES = [ACTIVITY_BEACH_DAY, ACTIVITY_HIKING];

// Below this normalized score the day is presented as "no good opportunity"
// rather than as a recommendation, even though the best available option is
// still named so the number can be judged.
export const GOOD_OPPORTUNITY_THRESHOLD = 50;

export const FORECAST_UNAVAILABLE_MESSAGE = "Forecast unavailable — could not reach the weather service.";
const NO_WINDOW_MESSAGE = "No usable outdoor window found for today.";

function scoreText(normalizedScore) {
  if (normalizedScore === null || normalizedScore === undefined) return "N/A";
  return `${normalizedScore}/100`;
}

function createRecommendation({ activity_profile, location_key, location_name, normalized_score, best_window }) {
  return {
    activity_profile,
    activity_label: getActivityProfileLabel(activity_profile),
    location_key,
    location_name,
    normalized_score,
    best_window,
    is_good: normalized_score !== null && normalized_score !== undefined && normalized_score >= GOOD_OPPORTUNITY_THRESHOLD,
    score_text: scoreText(normalized_score),
  };
}

function windowText(block) {
  const endTime = new Date(block.end.getTime() + 60 * 60 * 1000);
  return `${formatMadridTime(block.start)} - ${formatMadridTime(endTime)}`;
}

function recommendationFromResult(activityProfile, result, locations) {
  if (!result) {
    return createRecommendation({
      activity_profile: activityProfile,
      location_key: null,
      location_name: null,
      normalized_score: null,
      best_window: null,
    });
  }
  const locationName = result.location_key in locations ? locations[result.location_key].name : result.location_name;
  return createRecommendation({
    activity_profile: activityProfile,
    location_key: result.location_key,
    location_name: locationName,
    // raw_score is the optimal window's own quality, so the /100 shown next to a
    // window describes that window and not some unrelated whole-day aggregate.
    normalized_score: normalizeScore(Number(result.raw_score), activityProfile),
    best_window: windowText(result.optimal_block),
  });
}

// The ranking rewards duration and consistency as well as quality, so the top
// ranked candidate can have a below-threshold window while a lower ranked one
// clears it. Announcing "no good option" in that case is simply wrong, so any
// candidate that clears the threshold wins — the existing ranking still decides
// which of them is best. Only when every candidate is below the threshold is the
// overall best sub-threshold option shown as "no good option".
function selectBestCandidate(ranked, activityProfile) {
  const good = ranked.find((result) => normalizeScore(Number(result.raw_score), activityProfile) >= GOOD_OPPORTUNITY_THRESHOLD);
  return good ?? ranked[0] ?? null;
}

// One independent recommendation per activity profile: the single best location
// across every supplied location, ranked on its own merits for that profile.
export function buildDailyRecommendations(forecasts, forecastDate, locations, { rankFn = getTopLocationsForDate } = {}) {
  const locationCount = Math.max(Object.keys(forecasts).length, 1);
  return SUMMARY_ACTIVITY_PROFILES.map((activityProfile) => {
    const ranked = rankFn({ ...forecasts }, forecastDate, locationCount, activityProfile) ?? [];
    return recommendationFromResult(activityProfile, selectBestCandidate(ranked, activityProfile), locations);
  });
}

export function tierEmoji(normalizedScore) {
  if (normalizedScore === null || normalizedScore === undefined) return "⚪";
  if (normalizedScore >= 80) return "🟢";
  if (normalizedScore >= GOOD_OPPORTUNITY_THRESHOLD) return "🟡";
  return "🔴";
}

export function formatRecommendationLine(recommendation) {
  const { activity_label: label, location_name: name, best_window: window, score_text: score } = recommendation;
  if (recommendation.normalized_score === null || recommendation.normalized_score === undefined) {
    return `⚪ ${label}: no usable window today`;
  }
  if (!recommendation.is_good) {
    return `🔴 ${label}: no good option — best is ${name} ${window} (${score})`;
  }
  return `${tierEmoji(recommendation.normalized_score)} ${label}: ${name} ${window} (${score})`;
}

function coverageText(loaded, failed) {
  if (failed === 0) return `${loaded} location${loaded === 1 ? "" : "s"} checked`;
  return `${loaded} of ${loaded + failed} locations available`;
}

// `loaded`/`failed` separate "the forecast could not be fetched" from "the
// forecast was fetched and the weather is simply poor".
export function buildOutlookNotification(recommendations, { loaded = null, failed = 0 } = {}) {
  if (loaded === 0) {
    return { body: FORECAST_UNAVAILABLE_MESSAGE, largeBody: null, summaryText: "No forecast data" };
  }
  if (!recommendations || recommendations.length === 0) {
    return { body: NO_WINDOW_MESSAGE, largeBody: null, summaryText: null };
  }

  const lines = recommendations.map(formatRecommendationLine);
  // Coverage lives in summaryText only: Android renders both summaryText and
  // largeBody in the expanded notification, so repeating it there duplicates it.
  const coverage = loaded === null ? null : coverageText(loaded, failed);
  const body = lines.join("\n");

  return { body, largeBody: body, summaryText: coverage };
}
