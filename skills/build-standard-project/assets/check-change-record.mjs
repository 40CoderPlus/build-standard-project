import { execFileSync } from 'node:child_process';

const arguments_ = process.argv.slice(2);
const baseFlag = arguments_.indexOf('--base');
const base = baseFlag >= 0 ? arguments_[baseFlag + 1] : process.env.CHANGE_BASE_SHA;
if (!base) throw new Error('Pass --base <sha> or set CHANGE_BASE_SHA.');
if (/^0+$/.test(base)) {
  console.log('Change check skipped for the first repository push.');
  process.exit(0);
}

const git = (...args) => execFileSync('git', args, { encoding: 'utf8' });
git('rev-parse', '--verify', `${base}^{commit}`);

const normalize = (path) => path.replaceAll('\\', '/').replace(/^\.\//, '');
const changedFiles = git('diff', '--name-only', '--diff-filter=ACDMRT', base, '--')
  .split(/\r?\n/u)
  .filter(Boolean)
  .map(normalize);
const changedLiveFiles = git('diff', '--name-only', '--diff-filter=ACMRT', base, '--')
  .split(/\r?\n/u)
  .filter(Boolean)
  .map(normalize);

const isTest = (path) =>
  /(?:^|\/)(?:tests?|__tests__)(?:\/|$)/u.test(path) || /\.(?:test|spec)\.[^/]+$/u.test(path);
const isBehaviorSource = (path) =>
  /^(?:apps|packages)\//u.test(path) &&
  /\.(?:[cm]?[jt]sx?|css|scss|prisma|sql)$/u.test(path) &&
  !path.includes('/generated/') &&
  !isTest(path);

const sourceFiles = changedFiles.filter(isBehaviorSource);
const productFiles = changedFiles.filter(
  (path) => path.startsWith('docs/product/') && path !== 'docs/changes.md',
);
if (sourceFiles.length === 0 && productFiles.length === 0) {
  console.log('No product or behavior-source change requires a change record.');
  process.exit(0);
}
if (!changedFiles.includes('docs/changes.md')) {
  throw new Error('Update docs/changes.md for each requirement, optimization, bug, or behavior change.');
}

const addedLines = git('diff', '--unified=0', base, '--', 'docs/changes.md')
  .split(/\r?\n/u)
  .filter((line) => line.startsWith('+') && !line.startsWith('+++'))
  .map((line) => line.slice(1));
const entries = addedLines
  .join('\n')
  .split(/(?=^## )/mu)
  .filter((entry) => /^## \d{4}-\d{2}-\d{2} — \S/mu.test(entry));
if (entries.length === 0) throw new Error('Add a dated entry to docs/changes.md.');

const changedTests = new Set(changedLiveFiles.filter(isTest));
for (const entry of entries) {
  const title = entry.match(/^## (.+)$/mu)?.[1] ?? 'untitled entry';
  const type = entry.match(/^- Type:\s*(requirement|optimization|bug|maintenance)\s*$/mu)?.[1];
  const change = entry.match(/^- Change:\s*(\S.+)$/mu)?.[1];
  const tests = entry.match(/^- Tests:\s*(\S.+)$/mu)?.[1];
  if (!type || !change || !tests) {
    throw new Error(`Change entry "${title}" requires Type, Change, and Tests fields.`);
  }

  const citedTests = [...tests.matchAll(/`([^`]+)`/gu)]
    .map((match) => normalize(match[1]))
    .filter(isTest);
  if (type === 'bug' && citedTests.length === 0) {
    throw new Error(`Bug entry "${title}" must cite its regression test.`);
  }
  if (sourceFiles.length > 0 && !citedTests.some((path) => changedTests.has(path))) {
    throw new Error(`Change entry "${title}" must cite a test changed in this diff.`);
  }
}

console.log(
  `Change record passed: ${entries.length} entry/entries, ${sourceFiles.length} source file(s), ${changedTests.size} changed test(s).`,
);
