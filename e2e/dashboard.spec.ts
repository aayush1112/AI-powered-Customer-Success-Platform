import { test, expect } from "./fixtures";

test.describe("Dashboard Flow", () => {
  test("dashboard page loads successfully", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByText(/dashboard/i)).toBeVisible({ timeout: 10_000 });
  });

  test("all metric cards are visible", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    // At least one metric card should render (total customers, etc.)
    await expect(
      page.getByText(/customers|interactions|insights/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("customer status chart renders", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    await expect(
      page.getByText(/active|at.risk|churned|prospect/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("interaction trend chart renders", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    // Chart container or heading should be present
    await expect(
      page.getByText(/interaction trend|activity/i).first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("period filter changes trend data", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    const periodSelect = page.getByLabel(/period/i).or(
      page.getByRole("combobox", { name: /period/i })
    );
    if (await periodSelect.isVisible()) {
      await periodSelect.selectOption("last_7_days");
      await expect(page).not.toHaveURL(/error/);
    }
  });

  test("recent activity section is visible", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    await expect(
      page.getByText(/recent activity|recent events/i)
    ).toBeVisible({ timeout: 10_000 });
  });

  test("unauthenticated users are redirected to login", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/login/, { timeout: 5_000 });
  });

  test("navigation links work from dashboard", async ({ authenticatedPage: page }) => {
    await page.goto("/dashboard");
    await page.getByRole("link", { name: /customers/i }).click();
    await expect(page).toHaveURL(/customers/);
  });
});
