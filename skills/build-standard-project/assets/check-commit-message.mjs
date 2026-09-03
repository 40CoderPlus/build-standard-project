import { readFile } from 'node:fs/promises';

const messagePath = process.argv[2];
if (!messagePath) throw new Error('Commit message file path is required.');

const message = await readFile(messagePath, 'utf8');
const subject = message
  .split(/\r?\n/)
  .map((line) => line.trim())
  .find((line) => line && !line.startsWith('#'));

if (!subject) throw new Error('Commit message subject is required.');

const generatedSubject = /^(Merge\b|Revert\s+"|(?:fixup|squash)!\s)/;
const conventionalSubject = /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9][a-z0-9._/-]*\))?!?: .+/;

if (!generatedSubject.test(subject) && !conventionalSubject.test(subject)) {
  console.error('Commit message must follow Conventional Commits.');
  console.error('Example: fix(auth): reject an expired session');
  process.exit(1);
}

console.log('Commit message format passed.');
