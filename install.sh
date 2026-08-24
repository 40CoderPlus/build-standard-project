#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE="$SCRIPT_DIR/skills/build-standard-project"

if [ ! -f "$SOURCE/SKILL.md" ]; then
  printf '%s\n' "Invalid release: SKILL.md is missing from $SOURCE" >&2
  exit 1
fi

INSTALL_ROOT=${CODEX_HOME:-"$HOME/.codex"}
SKILLS_DIRECTORY="$INSTALL_ROOT/skills"
TARGET="$SKILLS_DIRECTORY/build-standard-project"

mkdir -p "$SKILLS_DIRECTORY"

BACKUP=''
if [ -e "$TARGET" ]; then
  TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
  BACKUP="$TARGET.backup-$TIMESTAMP"
  mv "$TARGET" "$BACKUP"
fi

if ! cp -R "$SOURCE" "$TARGET"; then
  if [ -n "$BACKUP" ] && [ ! -e "$TARGET" ] && [ -e "$BACKUP" ]; then
    mv "$BACKUP" "$TARGET"
  fi
  exit 1
fi

printf '%s\n' "Installed build-standard-project 1.6.0 to $TARGET"
if [ -n "$BACKUP" ]; then
  printf '%s\n' "Previous installation backed up to $BACKUP"
fi
printf '%s\n' 'The Skill will be available from the next Codex conversation.'
