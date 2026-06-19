import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";

test.describe("Authentication Flow", () => {
  test.describe("Registration", () => {
    test("successful registration redirects to login or dashboard", async ({
      page,
    }) => {
      const ts = Date.now();
      await page.goto(`${BASE}/register`);

      await page.getByLabel(/first name/i).fill("Test");
      await page.getByLabel(/last name/i).fill("User");
      await page.getByLabel(/email/i).fill(`reg_${ts}@e2e.test`);
      await page.getByLabel(/password/i).fill("Password123!");
      await page.getByRole("button", { name: /register|create account/i }).click();

      await expect(page).toHaveURL(/login|dashboard/);
    });

    test("duplicate email shows error message", async ({ page }) => {
      const email = `dup_${Date.now()}@e2e.test`;
      // Register once
      await page.goto(`${BASE}/register`);
      await page.getByLabel(/first name/i).fill("Dup");
      await page.getByLabel(/last name/i).fill("User");
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill("Password123!");
      await page.getByRole("button", { name: /register|create account/i }).click();
      await page.waitForURL(/login|dashboard/);

      // Register again with same email
      await page.goto(`${BASE}/register`);
      await page.getByLabel(/first name/i).fill("Dup");
      await page.getByLabel(/last name/i).fill("User");
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill("Password123!");
      await page.getByRole("button", { name: /register|create account/i }).click();

      await expect(page.getByText(/already exists|duplicate|conflict/i)).toBeVisible({
        timeout: 5_000,
      });
    });

    test("weak password shows validation error", async ({ page }) => {
      await page.goto(`${BASE}/register`);
      await page.getByLabel(/email/i).fill("weak@e2e.test");
      await page.getByLabel(/password/i).fill("weak");
      await page.getByRole("button", { name: /register|create account/i }).click();

      await expect(page.getByText(/password/i)).toBeVisible();
    });
  });

  test.describe("Login", () => {
    let email: string;
    const password = "Password123!";

    test.beforeEach(async ({ page }) => {
      email = `login_${Date.now()}@e2e.test`;
      await page.goto(`${BASE}/register`);
      await page.getByLabel(/first name/i).fill("Login");
      await page.getByLabel(/last name/i).fill("Test");
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill(password);
      await page.getByRole("button", { name: /register|create account/i }).click();
      await page.waitForURL(/login|dashboard/);
    });

    test("valid credentials redirect to dashboard", async ({ page }) => {
      if (!page.url().includes("dashboard")) {
        await page.goto(`${BASE}/login`);
        await page.getByLabel(/email/i).fill(email);
        await page.getByLabel(/password/i).fill(password);
        await page.getByRole("button", { name: /log in|sign in/i }).click();
      }
      await expect(page).toHaveURL(/dashboard|customers/);
    });

    test("wrong password shows error", async ({ page }) => {
      await page.goto(`${BASE}/login`);
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill("WrongPass1!");
      await page.getByRole("button", { name: /log in|sign in/i }).click();
      await expect(page.getByText(/invalid|incorrect|unauthorized/i)).toBeVisible({
        timeout: 5_000,
      });
    });

    test("unknown email shows error", async ({ page }) => {
      await page.goto(`${BASE}/login`);
      await page.getByLabel(/email/i).fill("nobody@notreal.test");
      await page.getByLabel(/password/i).fill("Password123!");
      await page.getByRole("button", { name: /log in|sign in/i }).click();
      await expect(page.getByText(/invalid|incorrect|unauthorized/i)).toBeVisible({
        timeout: 5_000,
      });
    });
  });

  test.describe("Protected routes", () => {
    test("unauthenticated access to /dashboard redirects to login", async ({
      page,
    }) => {
      await page.context().clearCookies();
      await page.goto(`${BASE}/dashboard`);
      await expect(page).toHaveURL(/login/);
    });

    test("unauthenticated access to /customers redirects to login", async ({
      page,
    }) => {
      await page.context().clearCookies();
      await page.goto(`${BASE}/customers`);
      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe("Logout", () => {
    test("logout clears session and redirects to login", async ({ page }) => {
      const ts = Date.now();
      const email = `logout_${ts}@e2e.test`;
      await page.goto(`${BASE}/register`);
      await page.getByLabel(/first name/i).fill("Logout");
      await page.getByLabel(/last name/i).fill("Test");
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).fill("Password123!");
      await page.getByRole("button", { name: /register|create account/i }).click();

      if (page.url().includes("login")) {
        await page.getByLabel(/email/i).fill(email);
        await page.getByLabel(/password/i).fill("Password123!");
        await page.getByRole("button", { name: /log in|sign in/i }).click();
        await page.waitForURL(/dashboard|customers/);
      }

      await page.getByRole("button", { name: /logout|sign out/i }).click();
      await expect(page).toHaveURL(/login/, { timeout: 5_000 });
    });
  });
});
