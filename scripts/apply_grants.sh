#!/usr/bin/env bash
set -euo pipefail
: "${AI_READONLY_PASSWORD_MANAGER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_CASHIER:?set this in your shell profile}"
: "${AI_READONLY_PASSWORD_WAREHOUSE:?set this in your shell profile}"
: "${MYSQL_ROOT_PASSWORD:=restaurant-root}"

for view in db/views/vw_ai_quanly.sql db/views/vw_ai_thungan.sql db/views/vw_ai_kho.sql; do
  docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" restaurant < "$view"
done

sed -e "s|__AI_READONLY_PASSWORD_MANAGER__|$AI_READONLY_PASSWORD_MANAGER|" \
    -e "s|__AI_READONLY_PASSWORD_CASHIER__|$AI_READONLY_PASSWORD_CASHIER|" \
    -e "s|__AI_READONLY_PASSWORD_WAREHOUSE__|$AI_READONLY_PASSWORD_WAREHOUSE|" \
  db/views/grants.sql.template \
  | docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" restaurant
