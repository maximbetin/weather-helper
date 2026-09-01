import test from "node:test";
import assert from "node:assert/strict";
import { LOCATIONS } from "../js/core/locations.js";

test("locations are the Asturias set, keyed consistently", () => {
  assert.equal(Object.keys(LOCATIONS).length, 13);
  for (const [key, location] of Object.entries(LOCATIONS)) {
    assert.equal(location.key, key);
    assert.equal(typeof location.name, "string");
    assert.equal(typeof location.lat, "number");
    assert.equal(typeof location.lon, "number");
  }
});
