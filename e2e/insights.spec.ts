import { test, expect } from "./fixtures";

test.describe("AI Insight Flow", () => {
  async function createInteraction(page: import("@playwright/test").Page, ts: number) {
    // Create customer
    await page.goto("/customers/new");
    await page.getByLabel(/company name/i).fill(`InsightCo_${ts}`);
    await page.getByLabel(/contact name/i).fill("Insight Contact");
    await page.getByLabel(/contact email/i).fill(`insight_${ts}@corp.test`);
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/customers/);

    // Create interaction with meaningful notes
    await page.goto("/interactions/new");
    await page.getByLabel(/title/i).fill(`Insight Meeting ${ts}`);
    const customerSelector = page.getByLabel(/customer/i);
    await customerSelector.click();
    await page.getByText(`InsightCo_${ts}`).click();
    await page.getByLabel(/notes/i).fill(
      "The customer expressed high satisfaction with the product. They are planning to " +
        "expand their usage to three additional teams. They raised concerns about API " +
        "documentation quality and requested a dedicated success manager."
    );
    await page.getByRole("button", { name: /create|save/i }).click();
    await page.waitForURL(/interactions/);

    // Navigate to the interaction detail
    await page.getByText(`Insight Meeting ${ts}`).click();
    await expect(page).toHaveURL(/interactions\/[a-f0-9-]+$/);
  }

  test("generate insight from interaction detail page", async ({
    authenticatedPage: page,
  }) => {
    const ts = Date.now();
    await createInteraction(page, ts);

    // Generate insight
    await page.getByRole("button", { name: /generate insight|analyse/i }).click();

    // Wait for insight section to appear
    await expect(
      page.getByText(/summary|sentiment|action items/i)
    ).toBeVisible({ timeout: 30_000 });
  });

  test("view existing insight shows sentiment and summary", async ({
    authenticatedPage: page,
  }) => {
    const ts = Date.now();
    await createInteraction(page, ts);

    // Generate
    await page.getByRole("button", { name: /generate insight|analyse/i }).click();
    await expect(page.getByText(/summary|sentiment/i)).toBeVisible({
      timeout: 30_000,
    });

    // After generation, insight card should be rendered
    await expect(
      page.getByText(/positive|negative|neutral/i)
    ).toBeVisible({ timeout: 5_000 });
  });

  test("regenerate insight replaces existing", async ({
    authenticatedPage: page,
  }) => {
    const ts = Date.now();
    await createInteraction(page, ts);

    // Generate first
    await page.getByRole("button", { name: /generate insight|analyse/i }).click();
    await expect(page.getByText(/summary|sentiment/i)).toBeVisible({
      timeout: 30_000,
    });

    // Regenerate
    await page.getByRole("button", { name: /regenerate|re-analyse/i }).click();
    // Insight should still be displayed after regeneration
    await expect(page.getByText(/summary|sentiment/i)).toBeVisible({
      timeout: 30_000,
    });
  });
});
