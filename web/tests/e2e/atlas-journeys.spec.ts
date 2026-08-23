import { expect, expectNoFakeChartLanguage, test } from "./fixtures";

const inflationQuestion = "How fast is inflation running now, and is it accelerating or decelerating?";
const inflationMomentum = "Inflation momentum: monthly and 3-month annualized";

test("information scent: home to active area to question to primary evidence", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1, name: "Explore the questions shaping Argentina's economy." })).toBeVisible();
  await expectNoFakeChartLanguage(page);
  await expect(page.getByRole("link", { name: /Fiscal Regime/i })).toHaveCount(0);

  await page.getByRole("link", { name: /Nominal Stabilization/i }).first().click();
  await expect(page).toHaveURL(/\/areas\/nominal-stabilization\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: "Nominal Stabilization" })).toBeVisible();
  await expectNoFakeChartLanguage(page);

  await page.getByRole("link", { name: inflationQuestion }).click();
  await expect(page).toHaveURL(/\/questions\/how-fast-is-inflation-running-now-and-is-it-accelerating-or-decelerating\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: inflationQuestion })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ways to look at it" })).toBeVisible();
  await expect(page.locator('img[data-plot-render="embed"]')).toHaveCount(3);
  await expect(page.getByText(/Data through 2026-/).first()).toBeVisible();
  await expect(page.getByText(/Source:/).first()).toBeVisible();
  await expectNoFakeChartLanguage(page);

  await page.getByRole("link", { name: "View chart" }).first().click();
  await expect(page).toHaveURL(/\/charts\/inflation-momentum-monthly-and-3-month-annualized\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: inflationMomentum })).toHaveCount(1);
  await expect(page.locator('img[data-plot-render="embed"]')).toBeVisible();
  await expect(page.getByText(/Data through 2026-07-01 · Source: Datos Argentina/)).toBeVisible();
  await expect(page.getByRole("link", { name: inflationQuestion })).toBeVisible();
});

test("search promotes real evidence and excludes semantic-only chart concepts", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Search the atlas/i }).click();

  const dialog = page.getByRole("dialog", { name: "Search the economic atlas" });
  const input = dialog.getByRole("textbox", { name: "Search questions, topics, charts, indicators, and areas" });
  await input.fill("gross reserves");

  const grossReservesChart = dialog.getByRole("option", { name: "Gross international reserves Chart" });
  await expect(grossReservesChart).toBeVisible();
  await expect(dialog.getByRole("option", { name: "Debt service versus reserves Chart" })).toHaveCount(0);

  await grossReservesChart.click();
  await expect(page).toHaveURL(/\/charts\/gross-international-reserves\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: "Gross international reserves" })).toBeVisible();
  await expect(page.locator('img[data-plot-render="embed"]')).toBeVisible();
  await expect(page.getByText(/Source: BCRA/)).toBeVisible();
});

test("keyboard search is labelled, focused, and opens a matching destination", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Control+K");

  const dialog = page.getByRole("dialog", { name: "Search the economic atlas" });
  const input = dialog.getByRole("textbox", { name: "Search questions, topics, charts, indicators, and areas" });
  await expect(input).toBeFocused();
  await input.fill("gross reserves");
  await expect(dialog.getByRole("option").first()).toBeVisible();

  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/topics\/gross-international-reserves\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: "Gross international reserves" })).toBeVisible();
});

test("direct evidence has page-owned title, freshness/source context, and related navigation", async ({ page }) => {
  await page.goto("/charts/headline-inflation-monthly-vs-year-over-year/");

  const title = "Headline inflation: monthly vs year-over-year";
  await expect(page.getByRole("heading", { level: 1, name: title })).toHaveCount(1);
  await expect(page.locator('img[data-plot-render="embed"]')).toHaveAttribute("alt", /Headline inflation: monthly vs year-over-year/);
  await expect(page.getByText(/Data through 2026-07-31 · Source: Datos Argentina, BCRA/)).toBeVisible();
  await expect(page.getByRole("link", { name: inflationQuestion })).toBeVisible();
  await expect(page.getByRole("link", { name: "Inflation" }).first()).toBeVisible();
  await expectNoFakeChartLanguage(page);
});

test("historical evidence is addressable but not promoted in search", async ({ page }) => {
  await page.goto("/charts/bcra-policy-rate-history/");

  await expect(page.getByRole("heading", { level: 1, name: "BCRA policy rate history" })).toBeVisible();
  await expect(page.getByText(/Historical evidence · Data through 2025-07-10 · Source: BCRA · stale source snapshot/)).toBeVisible();
  await expect(page.locator('img[data-plot-render="embed"]')).toBeVisible();

  await page.getByRole("button", { name: /Search the atlas/i }).click();
  const dialog = page.getByRole("dialog", { name: "Search the economic atlas" });
  await dialog.getByRole("textbox", { name: "Search questions, topics, charts, indicators, and areas" }).fill("policy rate history");
  await expect(dialog.getByRole("option", { name: "BCRA policy rate history Chart" })).toHaveCount(0);
});
