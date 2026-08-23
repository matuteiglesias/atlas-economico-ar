import { expect, expectNoFakeChartLanguage, expectNoHorizontalOverflow, test } from "./fixtures";

const inflationQuestion = "How fast is inflation running now, and is it accelerating or decelerating?";

test.use({
  viewport: { width: 390, height: 844 },
  isMobile: true,
  hasTouch: true,
});

test("mobile journey keeps navigation honest and reaches readable primary evidence", async ({ page }) => {
  await page.goto("/");
  await expectNoHorizontalOverflow(page);

  await page.getByRole("button", { name: "Open Explore menu" }).click();
  const menu = page.getByRole("dialog", { name: "Explore the atlas" });
  const areaNav = menu.getByRole("navigation", { name: "Economic areas" });
  await expect(areaNav.getByRole("link")).toHaveCount(2);
  await expect(areaNav.getByRole("link", { name: "Fiscal Regime" })).toHaveCount(0);

  await areaNav.getByRole("link", { name: "Nominal Stabilization" }).click();
  await expect(page).toHaveURL(/\/areas\/nominal-stabilization\/?$/);
  await expect(page.getByRole("heading", { level: 1, name: "Nominal Stabilization" })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await page.getByRole("link", { name: inflationQuestion }).click();
  await expect(page.getByRole("heading", { level: 1, name: inflationQuestion })).toBeVisible();
  await expect(page.locator('img[data-plot-render="embed"]').first()).toBeVisible();
  await expectNoFakeChartLanguage(page);
  await expectNoHorizontalOverflow(page);

  await page.getByRole("link", { name: "View chart" }).first().click();
  await expect(page.getByRole("heading", { level: 1, name: "Inflation momentum: monthly and 3-month annualized" })).toBeVisible();
  await expect(page.locator('img[data-plot-render="embed"]')).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
