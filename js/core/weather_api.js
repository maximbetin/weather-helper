const PROJECT_URL = "https://github.com/maximbetin/weather-helper";
export const USER_AGENT = `WeatherHelper (${PROJECT_URL})`;
export const API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete";
export const API_URL_COMPACT = "https://api.met.no/weatherapi/locationforecast/2.0/compact";

const REQUEST_TIMEOUT_SECONDS = 10;
const MIN_COMPLETE_TIMESERIES_LENGTH = 5;

function buildForecastUrl(baseUrl, location) {
  return `${baseUrl}?lat=${location.lat}&lon=${location.lon}`;
}

async function makeRequest(url) {
  // Not all fetch runtimes this app runs in (e.g. the background-runner worker)
  // support AbortController, so the timeout is enforced purely via Promise.race.
  let timeoutId;
  const timeoutPromise = new Promise((_resolve, reject) => {
    timeoutId = setTimeout(() => reject(new Error("Weather API request timed out")), REQUEST_TIMEOUT_SECONDS * 1000);
  });
  try {
    const response = await Promise.race([
      fetch(url, {
        method: "GET",
        headers: { "User-Agent": USER_AGENT },
      }),
      timeoutPromise,
    ]);
    if (!response.ok) {
      console.error(`Weather API request failed: ${url} (${response.status})`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`Weather API request failed: ${url} (${error})`);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
}

function getTimeseries(data) {
  return (data?.properties || {}).timeseries || [];
}

function hasCompleteForecast(data) {
  return data !== null && getTimeseries(data).length >= MIN_COMPLETE_TIMESERIES_LENGTH;
}

export async function fetchWeatherData(location) {
  let data = await makeRequest(buildForecastUrl(API_URL, location));
  if (!hasCompleteForecast(data)) {
    data = await makeRequest(buildForecastUrl(API_URL_COMPACT, location));
  }
  return data;
}
