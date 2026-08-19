import test from "node:test";
import assert from "node:assert/strict";
import { createRunnerBundle, validateRunnerBundle } from "../scripts/build-runner.mjs";

test("the generated background runner bundle parses as a classic script", async () => {
  const bundle = await createRunnerBundle();
  // Module syntax would throw in the runner's engine, which has no module loader.
  assert.doesNotMatch(bundle, /^\s*(import|export)\s/m);
  assert.doesNotThrow(() => validateRunnerBundle(bundle));
});

test("an invalid generated bundle fails the build with a clear message", () => {
  assert.throws(() => validateRunnerBundle("function broken( {"), /not a valid classic script/);
});
