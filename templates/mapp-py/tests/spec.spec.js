import { test, expect } from '@playwright/test';
import { getClientHost } from './setup.js';

/**
 * Spec loading tests for MAPP UI
 * 
 * These tests verify that the /api/spec endpoint is accessible
 * in both the crud and pagination test environments.
 */

test.describe('MAPP Spec Loading', () => {
  
  test('should load spec from crud environment', async ({ request }) => {
    // Load the MAPP_CLIENT_HOST from the crud environment file
    const crudHost = getClientHost('mapp-tests/crud.env');
    
    // Make request to /api/spec
    const response = await request.get(`${crudHost}/api/spec`);
    
    // Verify response is successful
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Parse and verify the spec structure
    const spec = await response.json();
    
    // Verify basic spec structure exists
    expect(spec).toHaveProperty('project');
    expect(spec).toHaveProperty('modules');
    expect(spec).toHaveProperty('client');
    
    // Verify project has expected properties
    expect(spec.project).toHaveProperty('name');
    expect(spec.project).toHaveProperty('use_builtin_modules');
    
    console.log(`Loaded spec from crud environment: ${crudHost}/api/spec`);
    console.log(`Project name: ${spec.project.name.lower_case}`);
  });

  test('should load spec from pagination environment', async ({ request }) => {
    // Load the MAPP_CLIENT_HOST from the pagination environment file
    const paginationHost = getClientHost('mapp-tests/pagination.env');
    
    // Make request to /api/spec
    const response = await request.get(`${paginationHost}/api/spec`);
    
    // Verify response is successful
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Parse and verify the spec structure
    const spec = await response.json();
    
    // Verify basic spec structure exists
    expect(spec).toHaveProperty('project');
    expect(spec).toHaveProperty('modules');
    expect(spec).toHaveProperty('client');
    
    // Verify project has expected properties
    expect(spec.project).toHaveProperty('name');
    expect(spec.project).toHaveProperty('use_builtin_modules');
    
    console.log(`Loaded spec from pagination environment: ${paginationHost}/api/spec`);
    console.log(`Project name: ${spec.project.name.lower_case}`);
  });
});
