import { expect, test as base, type Page } from "@playwright/test";

const browserErrors = new WeakMap<Page, string[]>();

export const test = base;
export { expect };

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  browserErrors.set(page, errors);

  page.on("pageerror", (error) => {
    errors.push(`pageerror: ${error.message}`);
  });

  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(`console.error: ${message.text()}`);
    }
  });
});

test.afterEach(async ({ page }) => {
  expect(browserErrors.get(page) ?? [], "unexpected browser errors").toEqual([]);
});

export async function expectNoFakeChartLanguage(page: Page) {
  await expect(page.getByText(/illustrative placeholder/i)).toHaveCount(0);
  await expect(page.getByText(/chart preview pending/i)).toHaveCount(0);
  await expect(page.getByText(/structure ready/i)).toHaveCount(0);
}

export async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "page should not require horizontal scrolling").toBeLessThanOrEqual(1);
}
