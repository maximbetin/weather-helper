import { madridHourOf } from "./timezone.js";

const SIGNIFICANT_RAIN_MM = 0.5;
const WARM_TEMP_C = 22;
const PLEASANT_TEMP_C = 18;
const COOL_TEMP_C = 10;

export function createHourlyWeather({
  time,
  temp = null,
  wind = null,
  cloud_coverage = null,
  precipitation_amount = null,
  precipitation_probability = null,
  symbol_code = null,
  relative_humidity = null,
  water_temp = null,
  wave_height = null,
  temp_score = 0,
  wind_score = 0,
  cloud_score = 0,
  precip_amount_score = 0,
  humidity_score = 0,
  water_temp_score = 0,
  wave_height_score = 0,
}) {
  const total_score =
    temp_score + wind_score + cloud_score + precip_amount_score + humidity_score + water_temp_score + wave_height_score;
  return {
    time,
    temp,
    wind,
    cloud_coverage,
    precipitation_amount,
    precipitation_probability,
    symbol_code,
    relative_humidity,
    water_temp,
    wave_height,
    temp_score,
    wind_score,
    cloud_score,
    precip_amount_score,
    humidity_score,
    water_temp_score,
    wave_height_score,
    hour: madridHourOf(time),
    total_score,
  };
}

function safeAverage(values) {
  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function describeTemperature(avgTemp) {
  if (avgTemp === null || avgTemp === undefined) return "Mixed";
  if (avgTemp >= WARM_TEMP_C) return "Warm";
  if (avgTemp >= PLEASANT_TEMP_C) return "Pleasant";
  if (avgTemp >= COOL_TEMP_C) return "Cool";
  return "Cold";
}

export function createDailyReport(date, daylightHours, locationName) {
  const report = {
    date,
    daylight_hours: daylightHours,
    location_name: locationName,
  };

  if (daylightHours.length === 0) {
    report.avg_score = -Infinity;
    report.likely_rain_hours = 0;
    report.min_temp = null;
    report.max_temp = null;
    report.avg_temp = null;
  } else {
    const temperatures = daylightHours.map((hour) => hour.temp).filter((temp) => temp !== null && temp !== undefined);
    const totalScore = daylightHours.reduce((sum, hour) => sum + hour.total_score, 0);
    report.likely_rain_hours = daylightHours.filter(
      (hour) => typeof hour.precipitation_amount === "number" && hour.precipitation_amount > SIGNIFICANT_RAIN_MM,
    ).length;
    report.min_temp = temperatures.length > 0 ? Math.min(...temperatures) : null;
    report.max_temp = temperatures.length > 0 ? Math.max(...temperatures) : null;
    report.avg_temp = safeAverage(temperatures);
    report.avg_score = totalScore / daylightHours.length;
  }

  Object.defineProperty(report, "weather_description", {
    enumerable: true,
    get() {
      if (report.likely_rain_hours > 0) return `Rain (${report.likely_rain_hours}h)`;
      return describeTemperature(report.avg_temp);
    },
  });

  return report;
}
