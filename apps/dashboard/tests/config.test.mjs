import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import nextConfig from "../next.config.mjs";

test("production build uses the standalone Docker output", () => {
  assert.equal(nextConfig.output, "standalone");
});

test("dashboard contains the operational workspace sections", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  for (const section of ["Customers", "Operations", "Quotes & bookings", "Conversations", "Knowledge", "Approvals"]) {
    assert.match(page, new RegExp(section));
  }
});
