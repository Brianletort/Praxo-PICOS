import { test, expect } from "@playwright/test";

test.describe("Onboarding", () => {
  test("shows welcome message", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByText(/Welcome to Praxo-PICOS/i)).toBeVisible();
  });

  test("shows first step content", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByText(/memory folder/i)).toBeVisible();
  });

  test("shows Next and Back buttons", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByRole("button", { name: /Next/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Back/i })).toBeVisible();
  });

  test("Back button is disabled on first step", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByRole("button", { name: /Back/i })).toBeDisabled();
  });
});
