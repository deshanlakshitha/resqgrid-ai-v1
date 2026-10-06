const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const http = require('node:http');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const ts = require('typescript');

function workerHarness() {
  const handlers = {};
  const cache = { put: jest.fn().mockResolvedValue(undefined) };
  const caches = {
    open: jest.fn().mockResolvedValue(cache),
    match: jest.fn().mockResolvedValue(undefined),
  };
  const response = { ok: true, type: 'basic', clone() { return this; } };
  const fetch = jest.fn().mockResolvedValue(response);
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../..', 'public/sw.js'), 'utf8'), {
    URL,
    Response: { error: () => ({ ok: false }) },
    self: {
      location: { origin: 'https://demo.test' },
      addEventListener: (name, handler) => { handlers[name] = handler; },
    },
    caches,
    fetch,
  });
  return { handlers, caches, cache, fetch };
}

function requestEvent(url, { method = 'GET', mode = 'cors', authorized = false } = {}) {
  return {
    request: { url, method, mode, headers: { has: () => authorized } },
    respondWith: jest.fn(),
    waitUntil: jest.fn(),
  };
}

describe('private responses stay outside the offline cache', () => {
  test.each([
    ['https://demo.test/api/v1/evidence/id/content', {}],
    ['https://demo.test/uploads/evidence/photo.png', {}],
    ['https://api.test/api/v1/incidents', {}],
    ['https://demo.test/login', { method: 'POST' }],
    ['https://demo.test/anything', { authorized: true }],
    ['https://demo.test/unknown-document', {}],
  ])('does not intercept %s', (url, options) => {
    const { handlers, caches, fetch } = workerHarness();
    const event = requestEvent(url, options);
    handlers.fetch(event);
    expect(event.respondWith).not.toHaveBeenCalled();
    expect(caches.open).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  test('navigation refreshes the shell from the network', async () => {
    const { handlers, cache, fetch } = workerHarness();
    const event = requestEvent('https://demo.test/login', { mode: 'navigate' });
    handlers.fetch(event);
    await event.respondWith.mock.calls[0][0];
    await Promise.all(event.waitUntil.mock.calls.map(([promise]) => promise));
    expect(fetch).toHaveBeenCalledWith(event.request);
    expect(cache.put).toHaveBeenCalled();
  });

  test('a failed navigation can use the cached shell', async () => {
    const { handlers, caches, fetch } = workerHarness();
    const shell = { ok: true };
    caches.match.mockResolvedValue(shell);
    fetch.mockRejectedValue(new Error('offline'));
    const event = requestEvent('https://demo.test/login', { mode: 'navigate' });
    handlers.fetch(event);
    expect(await event.respondWith.mock.calls[0][0]).toBe(shell);
  });
});

describe('MapLibre worker assets survive production bundling', () => {
  const webRoot = path.join(__dirname, '../..');

  test('publishes the installed worker and its relative shared module together', () => {
    const destination = fs.mkdtempSync(path.join(os.tmpdir(), 'resqgrid-map-worker-'));
    const distribution = path.join(path.dirname(require.resolve('maplibre-gl/package.json')), 'dist');
    try {
      execFileSync(process.execPath, [path.join(webRoot, 'scripts/prepare-maplibre.mjs'), destination]);
      for (const file of ['maplibre-gl-worker.mjs', 'maplibre-gl-shared.mjs']) {
        expect(fs.readFileSync(path.join(destination, file)))
          .toEqual(fs.readFileSync(path.join(distribution, file)));
      }
    } finally {
      fs.rmSync(destination, { recursive: true, force: true });
    }
  });

  test('prepares assets before development and both web and Capacitor builds', () => {
    const { scripts } = require('../../package.json');
    expect(scripts.predev).toBe('node scripts/prepare-maplibre.mjs');
    expect(scripts.prebuild).toBe('node scripts/prepare-maplibre.mjs');
  });

  test('configures a same-origin worker before returning the engine to either map', async () => {
    const engine = { setWorkerUrl: jest.fn() };
    const source = fs.readFileSync(path.join(__dirname, 'mapConfig.ts'), 'utf8');
    const { outputText } = ts.transpileModule(source, {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 },
    });
    const module = { exports: {} };
    vm.runInNewContext(outputText, {
      module,
      exports: module.exports,
      require: (name) => {
        if (name !== 'maplibre-gl') throw new Error(`Unexpected module: ${name}`);
        return engine;
      },
    });
    expect(await module.exports.loadMapLibre()).toBe(engine);
    expect(engine.setWorkerUrl).toHaveBeenCalledWith('/maplibre/maplibre-gl-worker.mjs');
  });
});

describe('security dependency overrides retain required tooling APIs', () => {
  test('Capacitor Xcode support still generates identifiers with patched uuid', () => {
    const capacitorRequire = createRequire(require.resolve('@capacitor/cli/package.json'));
    const xcode = capacitorRequire('xcode');
    const project = xcode.project('unused-test-project');
    project.hash = { project: { objects: {} } };
    const first = project.generateUuid();
    const second = project.generateUuid();
    expect(first).toMatch(/^[A-F0-9]{24}$/);
    expect(second).not.toBe(first);
  });

  test('Vercel HTTP client retains fetch and request compatibility', async () => {
    const vercelRequire = createRequire(require.resolve('vercel/package.json'));
    const { fetch, Request, Agent } = vercelRequire('undici');
    const server = http.createServer((_req, res) => {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ ok: true }));
    });
    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    const dispatcher = new Agent();
    try {
      const url = `http://127.0.0.1:${server.address().port}`;
      const response = await fetch(new Request(url), { dispatcher });
      expect(response.status).toBe(200);
      expect(await response.json()).toEqual({ ok: true });
    } finally {
      await dispatcher.close();
      await new Promise((resolve) => server.close(resolve));
    }
  });
});
