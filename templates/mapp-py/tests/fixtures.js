import { test as base, expect } from '@playwright/test';
import { getEnvSpec } from './env-helpers.js';

export const test = base.extend({
  crudEnv: [
    async ({}, use) => {
      const { host, spec } = await getEnvSpec('mapp-tests/crud.env', expect);
      await use({ host, spec });
    },
    { scope: 'worker' }
  ],
  paginationEnv: [
    async ({}, use) => {
      const { host, spec } = await getEnvSpec('mapp-tests/pagination.env', expect);
      await use({ host, spec });
    },
    { scope: 'worker' }
  ]
});
