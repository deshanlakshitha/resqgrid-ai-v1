import { copyFileSync, mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const source = path.join(path.dirname(require.resolve('maplibre-gl/package.json')), 'dist');
const destination = process.argv[2] || fileURLToPath(new URL('../public/maplibre/', import.meta.url));

// Next.js does not emit the worker's relative shared-module import automatically.
mkdirSync(destination, { recursive: true });
for (const file of ['maplibre-gl-worker.mjs', 'maplibre-gl-shared.mjs']) {
  copyFileSync(path.join(source, file), path.join(destination, file));
}
