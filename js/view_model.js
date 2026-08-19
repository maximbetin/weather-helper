import { fetchWeatherData } from "./core/weather_api.js";
import { processForecast, getAvailableDates, getTimeBlocksForDate, getTopLocationsForDate } from "./core/evaluation.js";
import { getActivityScore, getRatingInfo, normalizeScore, DEFAULT_ACTIVITY_PROFILE, ACTIVITY_PROFILE_LABELS } from "./core/scoring.js";
import { LOCATION_GROUPS } from "./core/locations.js";
import { formatTemperature, formatPercentage, formatPrecipitation, formatWindSpeed, formatTime } from "./core/presentation.js";

export const DOWNLOAD_ERROR = "Could not download forecast data. Check your connection and try again.";
export const PROCESSING_ERROR = "The forecast response did not contain usable weather data.";
export const UNEXPECTED_ERROR = "Could not load this forecast. Please try again.";

const DEFAULT_LOCATION_GROUP = "Asturias";

async function loadLocation(location) {
  try {
    const raw = await fetchWeatherData(location);
    if (raw === null) return { location, error: DOWNLOAD_ERROR };
    const processed = processForecast(raw, location.name);
    if (processed === null) return { location, error: PROCESSING_ERROR };
    return { location, forecast: processed };
  } catch (error) {
    console.error(`Unexpected error loading forecast for ${location.key}: ${error}`);
    return { location, error: UNEXPECTED_ERROR };
  }
}

async function loadLocations(locations, onProgress = null) {
  const entries = Object.entries(locations);
  const forecasts = {};
  const errors = {};
  let completed = 0;
  await Promise.all(
    entries.map(async ([key, location]) => {
      const result = await loadLocation(location);
      if (result.forecast) forecasts[key] = result.forecast;
      else errors[key] = result.error;
      completed += 1;
      if (onProgress) onProgress(completed, entries.length, location);
    }),
  );
  return { forecasts, errors };
}

function formatBestWindowDetails(block) {
  return `Temp: ${formatTemperature(block.temp)} · Wind: ${formatWindSpeed(block.wind)} · Clouds: ${formatPercentage(block.cloud)} · Rain: ${formatPrecipitation(block.precip)}`;
}

export class ForecastViewModel {
  constructor() {
    this.groupName = DEFAULT_LOCATION_GROUP;
    this.activityProfile = DEFAULT_ACTIVITY_PROFILE;
    this.selectedDate = null;
    this.selectedLocationKey = "";
    this.forecasts = {};
    this.errors = {};
  }

  get locations() {
    return LOCATION_GROUPS[this.groupName];
  }

  selectGroup(groupName) {
    if (!(groupName in LOCATION_GROUPS) || groupName === this.groupName) return;
    this.groupName = groupName;
    this._clearForecasts();
  }

  selectActivityProfile(profileKey) {
    if (!(profileKey in ACTIVITY_PROFILE_LABELS)) return;
    this.activityProfile = profileKey;
    if (!this.availableLocationKeys().includes(this.selectedLocationKey)) {
      this.selectedLocationKey = this._selectDefaultLocation();
    }
  }

  async load(onProgress = null) {
    const previousDate = this.selectedDate;
    const previousLocationKey = this.selectedLocationKey;

    const { forecasts, errors } = await loadLocations(this.locations, onProgress);
    this.forecasts = forecasts;
    this.errors = errors;

    const availableDates = this.availableDates();
    this.selectedDate = availableDates.includes(previousDate) ? previousDate : (availableDates[0] ?? null);

    if (this.availableLocationKeys().includes(previousLocationKey)) {
      this.selectedLocationKey = previousLocationKey;
    } else {
      this.selectedLocationKey = this._selectDefaultLocation();
    }

    return { forecasts, errors };
  }

  availableDates() {
    const dates = new Set();
    for (const processed of Object.values(this.forecasts)) {
      for (const d of getAvailableDates(processed)) dates.add(d);
    }
    return [...dates].sort();
  }

  selectDate(value) {
    if (!this.availableDates().includes(value)) return;
    this.selectedDate = value;
    if (!this.availableLocationKeys().includes(this.selectedLocationKey)) {
      this.selectedLocationKey = this._selectDefaultLocation();
    }
  }

  availableLocationKeys() {
    if (!this.selectedDate) return [];
    return Object.keys(this.forecasts).filter(
      (key) => key in this.locations && getTimeBlocksForDate(this.forecasts[key], this.selectedDate).length > 0,
    );
  }

  locationOptions() {
    return this.availableLocationKeys()
      .map((key) => [key, this.locations[key].name])
      .sort((a, b) => a[1].toLowerCase().localeCompare(b[1].toLowerCase()));
  }

  selectLocation(locationKey) {
    if (!this.availableLocationKeys().includes(locationKey)) return;
    this.selectedLocationKey = locationKey;
  }

  selectedLocation() {
    if (!this.selectedLocationKey) return null;
    const ranked = this.rankedLocations(Object.keys(this.forecasts).length);
    const found = ranked.find((item) => item.locationKey === this.selectedLocationKey);
    if (found) return found;
    if (this.availableLocationKeys().includes(this.selectedLocationKey)) {
      return this._unrankedLocationView(this.selectedLocationKey);
    }
    return null;
  }

  rankedLocations(topN = 10) {
    if (!this.selectedDate) return [];
    const ranked = getTopLocationsForDate(this.forecasts, this.selectedDate, topN, this.activityProfile);
    return ranked.map((item, index) => this._rankedLocationView(index + 1, item));
  }

  hourlyForecast(locationKey) {
    if (!this.selectedDate || !(locationKey in this.forecasts)) return [];
    return getTimeBlocksForDate(this.forecasts[locationKey], this.selectedDate).map((hour) => this._hourlyForecastView(hour));
  }

  _selectDefaultLocation() {
    const ranked = this.rankedLocations(1);
    if (ranked.length > 0) return ranked[0].locationKey;
    const keys = this.availableLocationKeys();
    return keys.length > 0 ? keys[0] : "";
  }

  _clearForecasts() {
    this.forecasts = {};
    this.errors = {};
    this.selectedDate = null;
    this.selectedLocationKey = "";
  }

  _rankedLocationView(rank, item) {
    const rawScore = Number(item.raw_score);
    const block = item.optimal_block;
    const endTime = new Date(block.end.getTime() + 60 * 60 * 1000);
    return {
      rank,
      locationKey: item.location_key,
      locationName: item.location_name,
      normalizedScore: normalizeScore(rawScore, this.activityProfile),
      rawScore,
      rating: getRatingInfo(rawScore, this.activityProfile),
      weatherDescription: item.weather_desc,
      bestWindow: `${formatTime(block.start)} - ${formatTime(endTime)}`,
      bestWindowDetails: formatBestWindowDetails(block),
      isRanked: true,
    };
  }

  _unrankedLocationView(locationKey) {
    const processed = this.forecasts[locationKey];
    const report = (processed?.day_scores || {})[this.selectedDate];
    return {
      rank: null,
      locationKey,
      locationName: this.locations[locationKey].name,
      normalizedScore: null,
      rawScore: null,
      rating: "N/A",
      weatherDescription: report ? report.weather_description : "Hourly forecast available",
      bestWindow: "",
      bestWindowDetails: "No single consistent window met the scoring thresholds today, but hourly details are available below.",
      isRanked: false,
    };
  }

  _hourlyForecastView(hour) {
    const rawScore = getActivityScore(hour, this.activityProfile);
    return {
      time: formatTime(hour.time),
      temperature: formatTemperature(hour.temp),
      wind: formatWindSpeed(hour.wind),
      clouds: formatPercentage(hour.cloud_coverage),
      precipitation: formatPrecipitation(hour.precipitation_amount),
      humidity: formatPercentage(hour.relative_humidity),
      normalizedScore: normalizeScore(rawScore, this.activityProfile),
      rating: getRatingInfo(rawScore, this.activityProfile),
    };
  }
}
