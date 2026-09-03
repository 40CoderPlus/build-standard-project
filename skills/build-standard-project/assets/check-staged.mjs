import { execFileSync } from 'node:child_process';
import path from 'node:path';

const staged = execFileSync(
  'git',
  ['diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z'],
  { encoding: 'utf8' },
)
  .split('\0')
  .filter(Boolean);

if (staged.length === 0) {
  console.log('No staged files require checks.');
  process.exit(0);
}

const pnpmCli = process.env.npm_execpath;
if (!pnpmCli) throw new Error('Invoke staged checks through pnpm.');

const extensionOf = (file) => path.extname(file).toLowerCase();
const codeExtensions = new Set(['.js', '.mjs', '.cjs', '.jsx', '.ts', '.mts', '.cts', '.tsx']);
const documentExtensions = new Set(['.md', '.mdx']);
const styleExtensions = new Set(['.css', '.scss']);
const formatExtensions = new Set([
  ...codeExtensions,
  ...documentExtensions,
  ...styleExtensions,
  '.json',
  '.jsonc',
  '.yaml',
  '.yml',
]);

const select = (extensions) => staged.filter((file) => extensions.has(extensionOf(file)));
const run = (label, command, commandArguments, files) => {
  if (files.length === 0) return;
  console.log(`${label}: ${files.length} staged file(s)`);
  execFileSync(process.execPath, [pnpmCli, 'exec', command, ...commandArguments, ...files], {
    stdio: 'inherit',
  });
};

run('Format', 'prettier', ['--check'], select(formatExtensions));
run('Code lint', 'eslint', ['--max-warnings=0'], select(codeExtensions));
run('Docs lint', 'markdownlint-cli2', [], select(documentExtensions));
run('Styles lint', 'stylelint', [], select(styleExtensions));

console.log('Staged-file quality checks passed.');
