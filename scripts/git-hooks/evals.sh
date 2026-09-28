#!/usr/bin/env bash
# Runs the AI evaluation suite (arguments) only when a staged file matches evals/watch.txt.
# A score under the threshold fails the tests, which blocks the commit.
set -uo pipefail

watch_file="evals/watch.txt"
staged="$(git diff --cached --name-only --diff-filter=ACMRD)"

if [ -f "$watch_file" ]; then
  patterns="$(grep -Ev '^\s*(#|$)' "$watch_file" || true)"
  if [ -z "$patterns" ] || ! printf '%s\n' "$staged" | grep -Eq -f <(printf '%s\n' "$patterns"); then
    echo "Éval IA sautée : aucun fichier surveillé par $watch_file n'est modifié."
    exit 0
  fi
fi

echo "Fichiers IA modifiés : lancement de l'évaluation."
exec "$(dirname "$0")/tests.sh" "$@"
