import { test, expect, type Page } from "@playwright/test";

/** Sidebar nav only — home page also has Quick Action links that substring-match (e.g. "Search Memory"). */
function sidebarNav(page: Page) {
  return page.locator("aside nav");
}

test.describe("Navigation", () => {
  test("sidebar shows all 6 navigation items", async ({ page }) => {
    await page.goto("/");
    const nav = sidebarNav(page);
    await expect(nav.getByRole("link", { name: /Home/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Assistant/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Memory/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Sources/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Health/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: /Settings/i })).toBeVisible();
  });

  test("clicking Health navigates to /health", async ({ page }) => {
    await page.goto("/");
    await sidebarNav(page).getByRole("link", { name: /Health/i }).click();
    await expect(page).toHaveURL(/\/health/);
    await expect(page.getByRole("heading", { name: /Health Center/i })).toBeVisible();
  });

  test("clicking Sources navigates to /sources", async ({ page }) => {
    await page.goto("/");
    await sidebarNav(page).getByRole("link", { name: /Sources/i }).click();
    await expect(page).toHaveURL(/\/sources/);
    await expect(page.getByRole("heading", { name: /Data Sources/i })).toBeVisible();
  });

  test("clicking Settings navigates to /settings", async ({ page }) => {
    await page.goto("/");
    await sidebarNav(page).getByRole("link", { name: /Settings/i }).click();
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.getByRole("heading", { name: /Settings/i })).toBeVisible();
  });

  test("clicking Memory navigates to /memory", async ({ page }) => {
    await page.goto("/");
    await sidebarNav(page).getByRole("link", { name: /Memory/i }).click();
    await expect(page).toHaveURL(/\/memory/);
    await expect(page.getByRole("heading", { name: /Memory/i })).toBeVisible();
  });
});
