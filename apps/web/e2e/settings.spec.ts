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

  test("shows configure subtitle", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByText(/Configure your personal/i)).toBeVisible();
  });
});
