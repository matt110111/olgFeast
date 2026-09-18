#!/bin/sh
# Explicit compose file avoids the repository's automatic development override.
set -eu
cd "$(dirname "$0")"
exec sudo docker compose --env-file docker.env -f docker-compose.yml "$@"
