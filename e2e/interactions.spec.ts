import { test, expect } from "./fixtures";

test.describe("Interaction Management Flow", () => {
  test("interaction list page loads", async ({ authenticatedPage: page }) => {
    await page.goto("/interactions");
    await expect(page).toHaveURL(/interactions/);
    // Table or empty state should be visible
    await expect(
      page.getByRole("table").or(page.getByText(/no interactions/i))
    ).toBeVisible({ timeout: 10_000 });
  });

  test("create interaction — happy path", async ({ authenticatedPage: page }) => {
    const ts = Date.now();

    // First create a customer to associate with
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(`InteractionCo_${ts}`);
    await page.getByLabel(/contact name/i).fill("Interaction Contact");
    await page.getByLabel(/contact email/i).fill(`int_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    // Create interaction
    await page.goto("/interactions/new");
    await page.getByLabel(/title/i).fill(`Q1 Review ${ts}`);

    // Select customer from dropdown/selector
    const customerSelector = page.getByLabel(/customer/i);
    await customerSelector.click();
    await page.getByText(`InteractionCo_${ts}`).click();

    // Set interaction type (Meeting is default)
    const typeSelect = page.getByLabel(/type/i);
    if (await typeSelect.isVisible()) {
      await typeSelect.selectOption("MEETING");
    }

    // Notes
    await page.getByLabel(/notes/i).fill(
      "Discussed product roadmap and renewal terms with key stakeholders."
    );

    await page.getByRole("button", { name: /create|save/i }).click();
    await expect(page).toHaveURL(/interactions/, { timeout: 10_000 });
    await expect(page.getByText(`Q1 Review ${ts}`)).toBeVisible({ timeout: 5_000 });
  });

  test("edit interaction updates the title", async ({ authenticatedPage: page }) => {
    const ts = Date.now();
    const original = `Original Title ${ts}`;
    const updated = `Updated Title ${ts}`;

    // Create customer + interaction
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(`EditIntCo_${ts}`);
    await page.getByLabel(/contact name/i).fill("Edit Contact");
    await page.getByLabel(/contact email/i).fill(`eint_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    await page.goto("/interactions/new");
    await page.getByLabel(/title/i).fill(original);
    const customerSelector = page.getByLabel(/customer/i);
    await customerSelector.click();
    await page.getByText(`EditIntCo_${ts}`).click();
    await page.getByLabel(/notes/i).fill(
      "Meeting notes for editing test scenario with sufficient length."
    );
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/interactions/);

    // Edit
    await page.getByText(original).click();
    await page.getByRole("link", { name: /edit/i }).click();
    await page.getByLabel(/title/i).clear();
    await page.getByLabel(/title/i).fill(updated);
    await page.getByRole("button", { name: /save|update/i }).click();

    await expect(page.getByText(updated)).toBeVisible({ timeout: 5_000 });
  });

  test("customer timeline shows created interaction", async ({
    authenticatedPage: page,
  }) => {
    const ts = Date.now();

    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(`TimelineCo_${ts}`);
    await page.getByLabel(/contact name/i).fill("Timeline");
    await page.getByLabel(/contact email/i).fill(`tl2_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    await page.goto("/interactions/new");
    await page.getByLabel(/title/i).fill(`Timeline Meeting ${ts}`);
    const customerSelector = page.getByLabel(/customer/i);
    await customerSelector.click();
    await page.getByText(`TimelineCo_${ts}`).click();
    await page.getByLabel(/notes/i).fill(
      "Notes about timeline test interaction with appropriate length."
    );
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/interactions/);

    // Navigate to customer detail and check timeline
    await page.goto("/customers");
    await page.getByText(`TimelineCo_${ts}`).click();
    await expect(page.getByText(`Timeline Meeting ${ts}`)).toBeVisible({
      timeout: 5_000,
    });
  });
});
