import { test, expect } from "@playwright/test";

test.describe("Memory Search", () => {
  test("shows search input", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByPlaceholder(/Search/i)).toBeVisible();
  });

  test("shows search button", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByRole("button", { name: /Search/i })).toBeVisible();
  });

  test("shows empty state before search", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByText(/Search your memories/i)).toBeVisible();
  });
});
