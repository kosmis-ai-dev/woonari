// T-013 / F06: preserve the board tool, while binding only the owned loopback instance.
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const value = (name) => args[args.indexOf(name) + 1];
const port = Number(value('--port'));
const instance = value('--instance');
if (!Number.isInteger(port) || port < 1024 || port > 65535 || !/^[a-f0-9]{32}$/.test(instance || '')) {
  throw new Error('Invalid Woonari dashboard invocation');
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const createServer = http.createServer;
http.createServer = function (...serverArgs) {
  const handler = serverArgs[serverArgs.length - 1];
  if (typeof handler !== 'function') throw new Error('Expected dashboard request handler');
  serverArgs[serverArgs.length - 1] = function (request, response) {
    response.setHeader('X-Woonari-Instance', instance);
    return handler.call(this, request, response);
  };
  return createServer.apply(this, serverArgs);
};
const listen = http.Server.prototype.listen;
http.Server.prototype.listen = function (requestedPort, callback) {
  if (requestedPort !== port) throw new Error('Unexpected dashboard port');
  return listen.call(this, port, '127.0.0.1', callback);
};
const tool = path.join(root, '.project/_tools/project-dashboard.mjs');
process.argv = [process.execPath, tool, 'serve', '--port', String(port), '--dir', path.join(root, '.project')];
await import(tool);
