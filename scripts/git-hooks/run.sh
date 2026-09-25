#!/usr/bin/env bash
# Runs a command inside the project's Docker Compose app container when it is up,
# otherwise on the host. Override the service with PRECOMMIT_SERVICE=<name>.
set -euo pipefail

compose_file=""
for f in compose.yaml compose.yml docker-compose.yaml docker-compose.yml; do
  [ -f "$f" ] && compose_file="$f" && break
done

if [ -n "$compose_file" ] && command -v docker >/dev/null 2>&1; then
  running="$(docker compose ps --status running --services 2>/dev/null || true)"
  for service in ${PRECOMMIT_SERVICE:-} app laravel.test php api backend; do
    if printf '%s\n' "$running" | grep -qx "$service"; then
      exec docker compose exec -T "$service" "$@"
    fi
  done
fi

exec "$@"
