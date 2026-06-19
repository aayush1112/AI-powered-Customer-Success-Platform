import { test, expect } from "./fixtures";

test.describe("Customer Management Flow", () => {
  test("customer list page loads with table", async ({ authenticatedPage: page }) => {
    await page.goto("/customers");
    await expect(page.getByRole("table")).toBeVisible({ timeout: 10_000 });
  });

  test("create customer — full happy path", async ({ authenticatedPage: page }) => {
    const ts = Date.now();
    const name = `E2E Corp ${ts}`;

    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(name);
    await page.getByLabel(/contact name/i).fill("E2E Contact");
    await page.getByLabel(/contact email/i).fill(`e2e_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();

    // Should redirect to customer list or detail
    await expect(page).toHaveURL(/customers/, { timeout: 10_000 });
    await expect(page.getByText(name)).toBeVisible({ timeout: 5_000 });
  });

  test("search filters the customer list", async ({ authenticatedPage: page }) => {
    const ts = Date.now();
    const name = `Searchable_${ts}`;

    // Create a uniquely named customer
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(name);
    await page.getByLabel(/contact name/i).fill("Search Contact");
    await page.getByLabel(/contact email/i).fill(`search_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    // Search
    await page.goto("/customers");
    const searchInput = page.getByPlaceholder(/search/i);
    await searchInput.fill(name);
    await expect(page.getByText(name)).toBeVisible({ timeout: 5_000 });
  });

  test("edit customer updates the record", async ({ authenticatedPage: page }) => {
    const ts = Date.now();
    const original = `EditMe_${ts}`;
    const updated = `Edited_${ts}`;

    // Create
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(original);
    await page.getByLabel(/contact name/i).fill("Edit Contact");
    await page.getByLabel(/contact email/i).fill(`edit_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    // Find and navigate to edit
    await page.goto("/customers");
    await page.getByText(original).click();
    await page.getByRole("link", { name: /edit/i }).click();

    await page.getByLabel(/company name/i).clear();
    await page.getByLabel(/company name/i).fill(updated);
    await page.getByRole("button", { name: /save|update/i }).click();

    await expect(page.getByText(updated)).toBeVisible({ timeout: 5_000 });
  });

  test("customer detail page shows interaction timeline", async ({
    authenticatedPage: page,
  }) => {
    const ts = Date.now();
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(`Timeline_${ts}`);
    await page.getByLabel(/contact name/i).fill("Timeline Contact");
    await page.getByLabel(/contact email/i).fill(`tl_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();

    await page.getByText(`Timeline_${ts}`).click();
    // Timeline section should be present (may be empty)
    await expect(page.getByText(/timeline|interactions/i)).toBeVisible({
      timeout: 5_000,
    });
  });
});
