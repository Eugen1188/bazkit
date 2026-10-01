import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, normalize, resolve, sep } from 'node:path';


const root = resolve(process.cwd(), 'dist', 'frontend', 'browser');
const port = Number(process.env.E2E_FRONTEND_PORT || 14200);
const apiRoot = process.env.E2E_API_ROOT || 'http://127.0.0.1:18000';
const websocketRoot = process.env.E2E_WEBSOCKET_ROOT || 'ws://127.0.0.1:18000';
const mimeTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url || '/', 'http://localhost').pathname);
  const relativePath = normalize(pathname).replace(/^([/\\])+/, '');
  let filePath = resolve(root, relativePath);
  if (!filePath.startsWith(`${root}${sep}`) && filePath !== root) {
    response.writeHead(400).end('Bad request');
    return;
  }
  if (!existsSync(filePath) || statSync(filePath).isDirectory()) {
    filePath = resolve(root, 'index.html');
  }
  if (filePath === resolve(root, 'index.html')) {
    const runtimeConfig = `<script>window.__BAZKIT_API_ROOT__=${JSON.stringify(apiRoot)};window.__BAZKIT_WEBSOCKET_ROOT__=${JSON.stringify(websocketRoot)};</script>`;
    const html = readFileSync(filePath, 'utf8').replace('</head>', `${runtimeConfig}</head>`);
    response.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
    });
    response.end(html);
    return;
  }
  response.writeHead(200, {
    'Content-Type': mimeTypes[extname(filePath)] || 'application/octet-stream',
    'Cache-Control': 'no-store',
  });
  createReadStream(filePath).pipe(response);
}).listen(port, '127.0.0.1', () => {
  process.stdout.write(`E2E frontend listening on http://127.0.0.1:${port}\n`);
});
