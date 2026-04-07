import { test, expect } from "@playwright/test";

test.describe("Settings", () => {
  test("shows settings heading", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: /Settings/i })).toBeVisible();
  });

  test("shows Basic/Advanced toggle", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("button", { name: /basic/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /advanced/i })).toBeVisible();
  });

  test("shows Memory Folder section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Memory Folder" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("shows Data Sources section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Data Sources" })).toBeVisible({
      timeout: 30_000,
    });
  });

  test("shows AI Provider section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "AI Provider" })).toBeVisible({
      timeout: 30_000,
    });
  });
});
