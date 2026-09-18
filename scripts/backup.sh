#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup="backups/olgfeast-$stamp.dump"
./olgfeast.sh exec -T db pg_dump -U olgfeast -d olgfeast -Fc > "$backup.tmp"
./olgfeast.sh exec -T db pg_restore --list < "$backup.tmp" > /dev/null
mv "$backup.tmp" "$backup"
echo "$backup"
