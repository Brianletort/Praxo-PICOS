import { test, expect } from "@playwright/test";

test.describe("Onboarding", () => {
  test("shows welcome message", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(page.getByText(/Welcome to Praxo-PICOS/i)).toBeVisible();
  });

  test("shows progress indicators", async ({ page }) => {
    await page.goto("/onboarding");
    const progressRow = page.locator("main .mb-8.flex.justify-center.gap-2");
    await expect(progressRow).toBeVisible();
    await expect(progressRow.locator("div.rounded-full")).toHaveCount(5);
  });

  test("Next button advances to step 2", async ({ page }) => {
    await page.goto("/onboarding");
    await expect(
      page.locator("main").getByRole("heading", { name: /Pick your Memory Folder/i })
    ).toBeVisible();
    await page.locator("main").getByRole("button", { name: /^Next$/ }).click();
    await expect(
      page.locator("main").getByRole("heading", { name: /Choose what to remember/i })
    ).toBeVisible();
  });

  test("Back button returns to step 1", async ({ page }) => {
    await page.goto("/onboarding");
    await page.locator("main").getByRole("button", { name: /^Next$/ }).click();
    await page.locator("main").getByRole("button", { name: /^Back$/ }).click();
    await expect(
      page.locator("main").getByRole("heading", { name: /Pick your Memory Folder/i })
    ).toBeVisible();
  });
});
