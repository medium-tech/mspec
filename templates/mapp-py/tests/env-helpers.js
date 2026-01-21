import { resolve } from 'path';
import { readFileSync } from 'fs';

export function parseEnvFile(filePath) {
  const envContent = readFileSync(filePath, 'utf-8');
  const env = {};
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        let value = valueParts.join('=');
        value = value.replace(/^['"]|['"]$/g, '');
        env[key] = value;
      }
    }
  });
  return env;
}

export async function getEnvSpec(envFileName, expect) {
  const path = resolve(process.cwd(), envFileName);
  const env = parseEnvFile(path);
  const host = env.MAPP_CLIENT_HOST;
  expect(host).toBeDefined();
  expect(host).toMatch(/^http:\/\/localhost:\d+$/);

  const response = await fetch(`${host}/api/spec`);
  expect(response.ok).toBeTruthy();
  expect(response.status).toBe(200);

  const spec = await response.json();
  expect(spec).toBeDefined();
  expect(spec.project).toBeDefined();
  expect(spec.modules).toBeDefined();

  return { host, spec };
}
