import { getTopLocationsForDate } from "./evaluation.js";
import { ACTIVITY_BEACH_DAY, ACTIVITY_HIKING, getActivityProfileLabel, normalizeScore } from "./scoring.js";
import { formatDateKeyShort, madridHourOf, madridMinuteOf } from "./timezone.js";

export const PRIORITY_LOCATION_KEYS = ["oviedo", "gijon"];
export const SUMMARY_ACTIVITY_PROFILES = [ACTIVITY_HIKING, ACTIVITY_BEACH_DAY];
export const DEFAULT_ALTERNATIVE_LIMIT = 3;

function scoreText(normalizedScore) {
  if (normalizedScore === null || normalizedScore === undefined) return "N/A";
  return `${normalizedScore}/100`;
}

function createDailySummaryRow({ activity_profile, activity_label, location_key, location_name, normalized_score, best_window, is_priority }) {
  return {
    activity_profile,
    activity_label,
    location_key,
    location_name,
    normalized_score,
    best_window,
    is_priority,
    get score_text() {
      return scoreText(normalized_score);
    },
  };
}

export function buildDailySummary(
  forecasts,
  forecastDate,
  locations,
  {
    priorityLocationKeys = PRIORITY_LOCATION_KEYS,
    alternativeLimit = DEFAULT_ALTERNATIVE_LIMIT,
    rankFn = getTopLocationsForDate,
  } = {},
) {
  const primaryRows = [];
  const alternativeRows = [];
  const priorityKeys = new Set(priorityLocationKeys.filter((key) => key in locations && key in forecasts));

  for (const activityProfile of SUMMARY_ACTIVITY_PROFILES) {
    const ranked = rankFn(
      { ...forecasts },
      forecastDate,
      Math.max(Object.keys(forecasts).length, 1),
      activityProfile,
    );
    const rankedByKey = new Map(ranked.map((item) => [item.location_key, item]));

    for (const locationKey of priorityLocationKeys) {
      if (!priorityKeys.has(locationKey)) continue;
      primaryRows.push(
        rowFromResult(activityProfile, locationKey, locations[locationKey].name, rankedByKey.get(locationKey) ?? null, {
          isPriority: true,
        }),
      );
    }

    const selectedAlternatives = ranked.filter((item) => !priorityKeys.has(item.location_key)).slice(0, Math.max(0, alternativeLimit));
    for (const item of selectedAlternatives) {
      const locationName = item.location_key in locations ? locations[item.location_key].name : item.location_name;
      alternativeRows.push(rowFromResult(activityProfile, item.location_key, locationName, item, { isPriority: false }));
    }
  }

  return [...primaryRows, ...alternativeRows];
}

function padEndTo(text, width) {
  return text.padEnd(width);
}

function padStartTo(text, width) {
  return text.padStart(width);
}

export function formatDailySummary(rows, { forecastDate = null } = {}) {
  if (!rows || rows.length === 0) return "No daily activity recommendations are available.";

  const activityHeader = "Activity";
  const locationHeader = "Location";
  const scoreHeader = "Score";
  const windowHeader = "Best time";

  const activityWidth = Math.max(activityHeader.length, ...rows.map((row) => row.activity_label.length));
  const locationWidth = Math.max(locationHeader.length, ...rows.map((row) => row.location_name.length));
  const scoreWidth = Math.max(scoreHeader.length, ...rows.map((row) => row.score_text.length));
  const windowWidth = Math.max(windowHeader.length, ...rows.map((row) => row.best_window.length));

  const lines = [
    summaryTitle(forecastDate),
    `${padEndTo(activityHeader, activityWidth)}  ${padEndTo(locationHeader, locationWidth)}  ${padStartTo(scoreHeader, scoreWidth)}  ${padEndTo(windowHeader, windowWidth)}`,
  ];

  const priorityRows = rows.filter((row) => row.is_priority);
  const alternativeRows = rows.filter((row) => !row.is_priority);

  for (const row of priorityRows) {
    lines.push(formatRow(row, activityWidth, locationWidth, scoreWidth, windowWidth));
  }
  if (alternativeRows.length > 0) {
    lines.push("", "Alternatives");
    for (const row of alternativeRows) {
      lines.push(formatRow(row, activityWidth, locationWidth, scoreWidth, windowWidth));
    }
  }
  return lines.join("\n");
}

function rowFromResult(activityProfile, locationKey, locationName, result, { isPriority }) {
  if (result === null || result === undefined) {
    return createDailySummaryRow({
      activity_profile: activityProfile,
      activity_label: getActivityProfileLabel(activityProfile),
      location_key: locationKey,
      location_name: locationName,
      normalized_score: null,
      best_window: "Not available",
      is_priority: isPriority,
    });
  }

  const block = result.optimal_block;
  const endTime = new Date(block.end.getTime() + 60 * 60 * 1000);
  const rawScore = Number(result.raw_score);
  return createDailySummaryRow({
    activity_profile: activityProfile,
    activity_label: getActivityProfileLabel(activityProfile),
    location_key: locationKey,
    location_name: locationName,
    normalized_score: normalizeScore(rawScore, activityProfile),
    best_window: `${formatMadridHourMinute(block.start)} - ${formatMadridHourMinute(endTime)}`,
    is_priority: isPriority,
  });
}

export function groupDailySummaryRows(rows) {
  const groups = new Map();
  for (const row of rows) {
    if (!groups.has(row.location_key)) {
      groups.set(row.location_key, { location_key: row.location_key, location_name: row.location_name, is_priority: row.is_priority, rows: [] });
    }
    groups.get(row.location_key).rows.push(row);
  }
  return [...groups.values()];
}

const NO_WINDOW_MESSAGE = "No good outdoor window found for today.";

export function tierEmoji(normalizedScore) {
  if (normalizedScore === null || normalizedScore === undefined) return "⚪";
  if (normalizedScore >= 80) return "🟢";
  if (normalizedScore >= 50) return "🟡";
  return "🔴";
}

function bestRow(rows) {
  const scored = rows.filter((row) => row.normalized_score !== null && row.normalized_score !== undefined);
  if (scored.length === 0) return null;
  return scored.reduce((best, row) => (row.normalized_score > best.normalized_score ? row : best));
}

export function buildOutlookNotification(rows) {
  const groups = groupDailySummaryRows(rows);
  if (groups.length === 0) {
    return { body: NO_WINDOW_MESSAGE, largeBody: null, summaryText: null };
  }

  const best = bestRow(rows);
  const body = best
    ? `${tierEmoji(best.normalized_score)} Best: ${best.activity_label} in ${best.location_name}, ${best.best_window} (${best.score_text})`
    : NO_WINDOW_MESSAGE;

  const largeBody = groups
    .map((group) => {
      const label = group.is_priority ? group.location_name : `Alt: ${group.location_name}`;
      const lines = group.rows.map((row) => `  ${tierEmoji(row.normalized_score)} ${row.activity_label} ${row.best_window} (${row.score_text})`);
      return [label, ...lines].join("\n");
    })
    .join("\n\n");

  const summaryText = `${groups.length} location${groups.length === 1 ? "" : "s"} checked`;

  return { body, largeBody, summaryText };
}

function formatMadridHourMinute(instant) {
  const hour = String(madridHourOf(instant)).padStart(2, "0");
  const minute = String(madridMinuteOf(instant)).padStart(2, "0");
  return `${hour}:${minute}`;
}

function formatRow(row, activityWidth, locationWidth, scoreWidth, windowWidth) {
  return `${padEndTo(row.activity_label, activityWidth)}  ${padEndTo(row.location_name, locationWidth)}  ${padStartTo(row.score_text, scoreWidth)}  ${padEndTo(row.best_window, windowWidth)}`;
}

function summaryTitle(forecastDate) {
  if (forecastDate === null || forecastDate === undefined) return "Daily outdoor windows";
  return `Daily outdoor windows for ${formatDateKeyShort(forecastDate)}`;
}
