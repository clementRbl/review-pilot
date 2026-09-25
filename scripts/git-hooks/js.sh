#!/usr/bin/env bash
# Runs a locally installed JS binary with the project's package manager (lockfile based).
set -euo pipefail

if [ -f pnpm-lock.yaml ]; then
  exec pnpm exec "$@"
elif [ -f yarn.lock ]; then
  exec yarn "$@"
elif [ -f bun.lock ] || [ -f bun.lockb ]; then
  exec bunx --no-install "$@"
else
  exec npx --no-install "$@"
fi
