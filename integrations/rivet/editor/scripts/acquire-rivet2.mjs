import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repository = 'https://github.com/valerypopoff/rivet2.0.git';
const revision = '4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053';
const editorRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const defaultCheckout = resolve(editorRoot, '..', 'spike', '.work', 'rivet2');
const checkout = resolve(process.env.WRIGHT_RIVET2_CHECKOUT || defaultCheckout);

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    encoding: 'utf8',
    stdio: options.capture ? 'pipe' : 'inherit',
  });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed with status ${result.status}`);
  }
  return (result.stdout || '').trim();
}

if (!existsSync(resolve(checkout, '.git'))) {
  run('git', ['clone', '--filter=blob:none', '--no-checkout', repository, checkout]);
  run('git', ['checkout', '--detach', revision], { cwd: checkout });
}

const actualRepository = run('git', ['remote', 'get-url', 'origin'], {
  cwd: checkout,
  capture: true,
});
const actualRevision = run('git', ['rev-parse', 'HEAD'], {
  cwd: checkout,
  capture: true,
});

if (![repository, repository.replace(/\.git$/, '')].includes(actualRepository)) {
  throw new Error(`Unexpected Rivet 2 origin: ${actualRepository}`);
}
if (actualRevision !== revision) {
  throw new Error(`Expected Rivet 2 ${revision}, received ${actualRevision}`);
}

process.stdout.write(`${JSON.stringify({ checkout, repository, revision })}\n`);
