#!/usr/bin/env bash
# Runs the full test suite given as arguments. Any failure blocks the commit.
# "No tests collected" (pytest exit code 5) is reported but does not block.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1

"$@"
status=$?
if [ "$status" -eq 5 ]; then
  echo "Aucun test trouvé : pense à en écrire."
  exit 0
fi
exit "$status"
