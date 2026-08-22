import test from "node:test";
import assert from "node:assert/strict";
import { formatWindSpeed } from "../js/core/presentation.js";

test("formatWindSpeed always converts source m/s values to km/h", () => {
  assert.equal(formatWindSpeed(0), "0.0 km/h");
  assert.equal(formatWindSpeed(10), "36.0 km/h");
  assert.equal(formatWindSpeed(null), "N/A");
});
