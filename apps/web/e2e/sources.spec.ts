import { test, expect } from "@playwright/test";

test.describe("Sources", () => {
  test("shows Data Sources heading", async ({ page }) => {
    await page.goto("/sources");
    await expect(page.getByRole("heading", { name: /Data Sources/i })).toBeVisible();
  });

  test("lists all five sources", async ({ page }) => {
    await page.goto("/sources");
    await expect(page.getByText("Loading sources…")).toBeHidden({ timeout: 30_000 });
    await expect(page.getByRole("heading", { name: /^mail$/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^calendar$/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^screen$/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^documents$/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^vault$/i })).toBeVisible();
  });
});
