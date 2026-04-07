import { test, expect } from "@playwright/test";

test.describe("Health Center", () => {
  test("shows Health Center heading", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByRole("heading", { name: /Health Center/i })).toBeVisible();
  });

  test("shows service status section", async ({ page }) => {
    await page.goto("/health");
    // Use the section h2 — subtitle also mentions "services" and would match loose text.
    await expect(page.getByRole("heading", { name: "Services" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("shows data flow section", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByRole("heading", { name: "Data Flow" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("shows repair actions", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByRole("heading", { name: "Repair Actions" })).toBeVisible({
      timeout: 30_000,
    });
  });
});
