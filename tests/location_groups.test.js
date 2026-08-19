import test from "node:test";
import assert from "node:assert/strict";
import { LOCATION_GROUPS, LOCATIONS, ASTURIAS_LOCATIONS, SPAIN_LOCATIONS, WORLDWIDE_LOCATIONS } from "../js/core/locations.js";

test("location groups structure", () => {
  assert.deepEqual(new Set(Object.keys(LOCATION_GROUPS)), new Set(["Asturias", "Spain", "Worldwide"]));
  assert.equal(LOCATION_GROUPS.Asturias, ASTURIAS_LOCATIONS);
  assert.equal(LOCATION_GROUPS.Spain, SPAIN_LOCATIONS);
  assert.equal(LOCATION_GROUPS.Worldwide, WORLDWIDE_LOCATIONS);
});

test("default locations are Asturias", () => {
  assert.equal(LOCATIONS, ASTURIAS_LOCATIONS);
});

test("location containment across groups", () => {
  for (const key of Object.keys(ASTURIAS_LOCATIONS)) {
    assert.ok(!(key in SPAIN_LOCATIONS));
  }
  const spainKeysInWorldwide = Object.keys(SPAIN_LOCATIONS).filter((key) => key in WORLDWIDE_LOCATIONS);
  assert.deepEqual(spainKeysInWorldwide, ["madrid"]);
  assert.equal(Object.keys(SPAIN_LOCATIONS).length, 19);
  assert.equal(Object.keys(WORLDWIDE_LOCATIONS).length, 13);
  assert.equal(Object.keys(ASTURIAS_LOCATIONS).length, 13);
});
