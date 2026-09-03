> This file extends [common/testing.md](../common/testing.md) with web-specific testing content.

# Web Testing Rules

## Priority Order

### 1. Visual Regression

- Screenshot key breakpoints: 320, 768, 1024, 1440
- Test hero sections, scrollytelling sections, and meaningful states
- Use Playwright screenshots for visual-heavy work
- If both themes exist, test both

### 2. Accessibility

- Run axe-core in CI (jest-axe, or @axe-core/playwright for rendered pages). The rules
  `aria-required-children`, `aria-required-parent` and `aria-dialog-name` catch the
  container-role and unnamed-dialog defects that human review misses - six of those
  shipped through review in one project. Prose does not close a CI gap
- Test keyboard navigation
- Verify reduced-motion behavior
- Verify color contrast, and re-verify after a *background* change, not only after a text change

### 3. Performance

- Run Lighthouse or equivalent against meaningful pages
- Keep CWV targets from [performance.md](performance.md)

### 4. Cross-Browser

- Minimum: Chrome, Firefox, Safari
- Test scrolling, motion, and fallback behavior

### 5. Responsive

- Test 320, 375, 768, 1024, 1440, 1920
- Verify no overflow
- Verify touch interactions

## E2E Shape

```ts
import { test, expect } from '@playwright/test';

test('landing hero loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toBeVisible();
});
```

- Avoid flaky timeout-based assertions
- Prefer deterministic waits

## Unit Tests

- Run the production build, not only the test runner. A test runner's module resolution
  is not the bundler's, so a green suite does not prove an import resolves in the built
  output
- Test utilities, data transforms, and custom hooks
- For highly visual components, visual regression often carries more signal than brittle markup assertions
- Visual regression supplements coverage targets; it does not replace them
