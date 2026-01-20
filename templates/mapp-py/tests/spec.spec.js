import { test, expect } from '@playwright/test';
import { config } from 'dotenv';
import { resolve } from 'path';
import { readFileSync } from 'fs';

// Helper function to parse env file
function parseEnvFile(filePath) {
  try {
    const envContent = readFileSync(filePath, 'utf-8');
    const env = {};
    envContent.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          let value = valueParts.join('=');
          // Remove quotes if present
          value = value.replace(/^["']|["']$/g, '');
          env[key] = value;
        }
      }
    });
    return env;
  } catch (error) {
    throw new Error(`Failed to read env file ${filePath}: ${error.message}`);
  }
}

test.describe('MAPP Spec Loading', () => {
  
  test('should load spec from crud environment', async ({ request }) => {
    // Load crud environment variables
    const crudEnvPath = resolve(process.cwd(), 'mapp-tests/crud.env');
    const crudEnv = parseEnvFile(crudEnvPath);
    
    const host = crudEnv.MAPP_CLIENT_HOST;
    expect(host).toBeDefined();
    expect(host).toMatch(/^http:\/\/localhost:\d+$/);
    
    // Make request to /api/spec
    const response = await request.get(`${host}/api/spec`);
    
    // Verify response
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Verify spec structure
    const spec = await response.json();
    expect(spec).toBeDefined();
    expect(spec.project).toBeDefined();
    expect(spec.modules).toBeDefined();
  });

  test('should load spec from pagination environment', async ({ request }) => {
    // Load pagination environment variables
    const paginationEnvPath = resolve(process.cwd(), 'mapp-tests/pagination.env');
    const paginationEnv = parseEnvFile(paginationEnvPath);
    
    const host = paginationEnv.MAPP_CLIENT_HOST;
    expect(host).toBeDefined();
    expect(host).toMatch(/^http:\/\/localhost:\d+$/);
    
    // Make request to /api/spec
    const response = await request.get(`${host}/api/spec`);
    
    // Verify response
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    // Verify spec structure
    const spec = await response.json();
    expect(spec).toBeDefined();
    expect(spec.project).toBeDefined();
    expect(spec.modules).toBeDefined();
  });
  
});
