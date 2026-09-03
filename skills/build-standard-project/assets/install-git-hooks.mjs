import { execFileSync } from 'node:child_process';
import { chmod } from 'node:fs/promises';

let insideWorkTree = false;
try {
  insideWorkTree =
    execFileSync('git', ['rev-parse', '--is-inside-work-tree'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim() === 'true';
} catch {
  // Package installation can run from an archive or container context without Git metadata.
}

if (!insideWorkTree) {
  console.log('Git metadata is unavailable; hook installation skipped.');
  process.exit(0);
}

if (process.platform !== 'win32') {
  await Promise.all([
    chmod('.githooks/pre-commit', 0o755),
    chmod('.githooks/commit-msg', 0o755),
  ]);
}

execFileSync('git', ['config', '--local', 'core.hooksPath', '.githooks'], {
  stdio: 'inherit',
});
console.log('Git commit hooks installed.');
