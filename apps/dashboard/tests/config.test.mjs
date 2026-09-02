import assert from "node:assert/strict";
import test from "node:test";
import nextConfig from "../next.config.mjs";

test("production build uses the standalone Docker output", () => {
  assert.equal(nextConfig.output, "standalone");
});
