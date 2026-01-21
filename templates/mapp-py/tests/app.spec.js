import { test } from './fixtures.js';
import { expect } from '@playwright/test';

test('confirm test setup', async ({ crudEnv, paginationEnv }) => {
  expect(crudEnv.spec).toEqual(paginationEnv.spec);
  expect(crudEnv.host).not.toEqual(paginationEnv.host);
});
