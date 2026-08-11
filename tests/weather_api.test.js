import test from "node:test";
import assert from "node:assert/strict";
import { USER_AGENT, API_URL_COMPACT, fetchWeatherData } from "../js/core/weather_api.js";

function fakeResponse(ok, jsonValue, { jsonError = null, status = 200 } = {}) {
  return {
    ok,
    status,
    json: async () => {
      if (jsonError) throw jsonError;
      return jsonValue;
    },
  };
}

function timeseriesOfLength(n) {
  return { properties: { timeseries: Array.from({ length: n }, () => ({ time: "2024-03-15T10:00:00Z" })) } };
}

function mockFetchSequence(t, responders) {
  const calls = [];
  const original = globalThis.fetch;
  let i = 0;
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    const responder = responders[i++];
    return responder();
  };
  t.after(() => {
    globalThis.fetch = original;
  });
  return calls;
}

const location = { key: "test", name: "Test", lat: 40.0, lon: -3.0 };

test("fetch weather data returns null when both endpoints fail", async (t) => {
  mockFetchSequence(t, [
    () => fakeResponse(false, null, { status: 500 }),
    () => fakeResponse(false, null, { status: 500 }),
  ]);

  const result = await fetchWeatherData(location);
  assert.equal(result, null);
});

test("fetch weather data returns null on network error for both endpoints", async (t) => {
  mockFetchSequence(t, [
    () => Promise.reject(new Error("Network error")),
    () => Promise.reject(new Error("Network error")),
  ]);

  const result = await fetchWeatherData(location);
  assert.equal(result, null);
});

test("fetch weather data success uses complete endpoint and sends user agent header", async (t) => {
  const mockData = timeseriesOfLength(10);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, mockData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, mockData);
  assert.ok(result.properties.timeseries.length >= 5);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.headers["User-Agent"], USER_AGENT);
});

test("fetch weather data falls back to compact endpoint when complete is insufficient", async (t) => {
  const insufficientData = timeseriesOfLength(1);
  const sufficientData = timeseriesOfLength(6);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, insufficientData), () => fakeResponse(true, sufficientData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, sufficientData);
  assert.equal(calls.length, 2);
  assert.ok(calls[1].url.startsWith(API_URL_COMPACT));
});

test("fetch weather data returns null when json parsing fails on both endpoints", async (t) => {
  mockFetchSequence(t, [
    () => fakeResponse(true, null, { jsonError: new Error("Invalid JSON") }),
    () => fakeResponse(true, null, { jsonError: new Error("Invalid JSON") }),
  ]);

  const result = await fetchWeatherData(location);
  assert.equal(result, null);
});

test("fetch weather data returns null on http error status for both endpoints", async (t) => {
  mockFetchSequence(t, [
    () => fakeResponse(false, null, { status: 404 }),
    () => fakeResponse(false, null, { status: 404 }),
  ]);

  const result = await fetchWeatherData(location);
  assert.equal(result, null);
});

test("fetch weather data falls back when complete endpoint has empty timeseries", async (t) => {
  const emptyData = { properties: { timeseries: [] } };
  const sufficientData = timeseriesOfLength(6);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, emptyData), () => fakeResponse(true, sufficientData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, sufficientData);
  assert.equal(calls.length, 2);
});

test("fetch weather data falls back when complete endpoint has no properties", async (t) => {
  const noPropertiesData = { other_key: "value" };
  const sufficientData = timeseriesOfLength(6);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, noPropertiesData), () => fakeResponse(true, sufficientData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, sufficientData);
  assert.equal(calls.length, 2);
});

test("fetch weather data falls back when complete endpoint has null properties", async (t) => {
  const nullPropertiesData = { properties: null };
  const sufficientData = timeseriesOfLength(6);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, nullPropertiesData), () => fakeResponse(true, sufficientData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, sufficientData);
  assert.equal(calls.length, 2);
});

test("fetch weather data returns compact result when both endpoints are insufficient", async (t) => {
  const insufficientData = timeseriesOfLength(1);
  const calls = mockFetchSequence(t, [() => fakeResponse(true, insufficientData), () => fakeResponse(true, insufficientData)]);

  const result = await fetchWeatherData(location);
  assert.deepEqual(result, insufficientData);
  assert.equal(calls.length, 2);
});
