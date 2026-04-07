import { test, expect } from "@playwright/test";

test.describe("Health Center", () => {
  test("shows Health Center heading", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByRole("heading", { name: /Health Center/i })).toBeVisible();
  });

  test("shows subheading", async ({ page }) => {
    await page.goto("/health");
    await expect(page.getByText(/Monitor services/i)).toBeVisible();
  });
});
