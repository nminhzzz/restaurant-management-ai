#!/usr/bin/env bash
set -euo pipefail
: "${AI_READONLY_PASSWORD_MANAGER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_CASHIER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_WAREHOUSE:?set this in your shell profile}"
: "${MYSQL_ROOT_PASSWORD:=restaurant-root}"

# Force the client charset/collation: a locale-detected latin1 client silently corrupts the Vietnamese
# literals inside the view definitions, and a default utf8mb4_0900_ai_ci connection collation makes
# the UNION branches fail with "Illegal mix of collations" against the unicode_ci columns.
MYSQL_CLIENT=(mysql -uroot -p"$MYSQL_ROOT_PASSWORD" --default-character-set=utf8mb4
  --init-command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci" restaurant)

for view in db/views/vw_ai_quanly.sql db/views/vw_ai_thungan.sql db/views/vw_ai_kho.sql; do
  docker compose exec -T db "${MYSQL_CLIENT[@]}" < "$view"
done

sed -e "s|__AI_READONLY_PASSWORD_MANAGER__|$AI_READONLY_PASSWORD_MANAGER|" \
    -e "s|__AI_READONLY_PASSWORD_CASHIER__|$AI_READONLY_PASSWORD_CASHIER|" \
    -e "s|__AI_READONLY_PASSWORD_WAREHOUSE__|$AI_READONLY_PASSWORD_WAREHOUSE|" \
  db/views/grants.sql.template \
  | docker compose exec -T db "${MYSQL_CLIENT[@]}"
