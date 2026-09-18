Current deployment: event-tablets modernization based on main commit below.
See [Event guide](docs/EVENT-GUIDE.md) for operation, verification, and recovery.

# Deployment on raspi5

Source: `matt110111/olgFeast`, branch `main`, commit
`1d68b8487e3fdad24d3064c573f661ac64d241be`.

Open http://192.168.8.163:3000 on the local network. The frontend proxies
API and WebSocket traffic. Backend diagnostics are available on the box at
http://127.0.0.1:8000/health and http://127.0.0.1:8000/docs.

Credentials are in `deployment_credentials.txt` (owner-readable only).
Database, Redis, and signing secrets are in `docker.env` (owner-readable only).
Keep these files private. PostgreSQL and Redis use persistent Docker volumes
and have no published host ports. The backend is bound to loopback.

From `/home/matthew/olgfeast`:

```sh
./olgfeast.sh ps
./olgfeast.sh logs --tail=100 -f
./olgfeast.sh restart
./olgfeast.sh stop
./olgfeast.sh up -d --wait
```

Docker starts at boot; all four containers use `restart: unless-stopped`.
After intentionally stopping containers, use `up -d --wait` to start them again.

The local changes fix Redis health checks, use same-origin API/WebSocket URLs,
allow WebSockets in the frontend content security policy, install frontend
dependencies from the lockfile, and keep database services private.
The lockfile also includes the missing optional Tailwind YAML dependency.
Use `git diff` to review these changes before updating the checkout.

Always use `olgfeast.sh` or explicitly pass `-f docker-compose.yml` and
`--env-file docker.env`. The automatic `docker-compose.override.yml` starts
development servers. Do not rerun `first_time_setup.sh`: it begins by deleting
database volumes. Do not use `down --volumes` unless you intend to erase data.

Back up the database before updates:

```sh
mkdir -p backups
chmod 700 backups
umask 077
./olgfeast.sh exec -T db pg_dump -U olgfeast -d olgfeast > backups/olgfeast.sql
```

This deployment uses HTTP on the local network. A public domain and HTTPS
have not been configured.

Verified on 2026-09-17: all four containers healthy; LAN frontend HTTP 200;
frontend assets and SPA routing; admin and customer login; role permissions;
13 seeded menu items; customer cart add/read/remove; and all three proxied
WebSocket channels responding to ping. Docker is enabled at boot and each
container has its restart policy configured. A host reboot was not performed.
