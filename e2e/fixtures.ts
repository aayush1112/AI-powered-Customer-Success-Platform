import { test as base, type Page } from "@playwright/test";

const API = process.env.API_URL ?? "http://localhost:8000/api/v1";

export type TestFixtures = {
  authenticatedPage: Page;
  adminPage: Page;
};

/** Register a new user, log them in, and return an authenticated page context. */
async function loginAs(
  page: Page,
  email: string,
  password: string,
  role: "MANAGER" | "ADMIN" = "MANAGER"
): Promise<void> {
  // For MANAGER: use the UI registration flow
  // For ADMIN: seed via API directly (requires a pre-existing admin token in CI)
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /log in|sign in/i }).click();
  await page.waitForURL(/dashboard|customers/);
}

export const test = base.extend<TestFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const ts = Date.now();
    const email = `e2e_mgr_${ts}@playwright.test`;
    const password = "Password123!";

    // Register
    await page.goto("/register");
    await page.getByLabel(/first name/i).fill("E2E");
    await page.getByLabel(/last name/i).fill("Manager");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /register|create account/i }).click();
    await page.waitForURL(/login|dashboard/);

    // Login (in case registration redirects to /login)
    if (page.url().includes("/login")) {
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill(password);
      await page.getByRole("button", { name: /log in|sign in/i }).click();
      await page.waitForURL(/dashboard|customers/);
    }

    await use(page);
  },

  adminPage: async ({ page }, use) => {
    // Admin login — assumes test admin credentials are set via env vars
    const email = process.env.E2E_ADMIN_EMAIL ?? "admin@e2e.test";
    const password = process.env.E2E_ADMIN_PASSWORD ?? "Password123!";
    await loginAs(page, email, password, "ADMIN");
    await use(page);
  },
});

export { expect } from "@playwright/test";
