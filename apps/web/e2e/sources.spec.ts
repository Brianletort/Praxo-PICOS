import { test, expect } from "@playwright/test";

test.describe("Sources", () => {
  test("shows Data Sources heading", async ({ page }) => {
    await page.goto("/sources");
    await expect(page.getByRole("heading", { name: /Data Sources/i })).toBeVisible();
  });

  test("shows manage description", async ({ page }) => {
    await page.goto("/sources");
    await expect(page.getByText(/Manage where your memories/i)).toBeVisible();
  });
});
