import { readFileSync } from 'fs';
import { resolve } from 'path';

/**
 * Parse a simple .env file and return key-value pairs
 * @param {string} envPath - Path to the .env file
 * @returns {Object} Environment variables as key-value pairs
 */
export function loadEnvFile(envPath) {
    const fullPath = resolve(envPath);
    const content = readFileSync(fullPath, 'utf-8');
    const env = {};
    
    content.split('\n').forEach(line => {
        // Skip comments and empty lines
        line = line.trim();
        if (!line || line.startsWith('#')) {
            return;
        }
        
        // Parse KEY=VALUE or KEY="VALUE"
        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
            const key = match[1].trim();
            let value = match[2].trim();
            
            // Remove surrounding quotes if present
            if ((value.startsWith('"') && value.endsWith('"')) ||
                (value.startsWith("'") && value.endsWith("'"))) {
                value = value.slice(1, -1);
            }
            
            env[key] = value;
        }
    });
    
    return env;
}

/**
 * Get the MAPP_CLIENT_HOST from an env file
 * @param {string} envPath - Path to the .env file
 * @returns {string} The MAPP_CLIENT_HOST value
 */
export function getClientHost(envPath) {
    const env = loadEnvFile(envPath);
    const host = env.MAPP_CLIENT_HOST;
    
    if (!host) {
        throw new Error(`MAPP_CLIENT_HOST not found in ${envPath}`);
    }
    
    return host;
}
