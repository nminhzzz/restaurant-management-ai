#!/usr/bin/env bash
# Prepare disposable MySQL schemas and least-privilege AI accounts for integration.
set -euo pipefail
: "${MYSQL_CONTAINER:?Set MYSQL_CONTAINER to the test MySQL container ID/name}"
: "${MYSQL_ROOT_PASSWORD:?Set MYSQL_ROOT_PASSWORD for the test MySQL instance}"
cd "$(dirname "$0")/.."

mysql_root() {
  docker exec -i -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" "$MYSQL_CONTAINER" mysql -uroot "$@"
}

# Fixed names prevent this helper from selecting an arbitrary application schema.
mysql_root <<'SQL'
SET GLOBAL log_bin_trust_function_creators = 1;
CREATE DATABASE IF NOT EXISTS restaurant_integration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS restaurant_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON restaurant_integration.* TO 'restaurant'@'%';
GRANT ALL PRIVILEGES ON restaurant_test.* TO 'restaurant'@'%';
SQL

for schema in restaurant_integration restaurant_test; do
  (
    cd apps/api
    DATABASE_URL="mysql+asyncmy://restaurant:restaurant@127.0.0.1:3306/$schema?charset=utf8mb4" \
      uv run alembic upgrade head
  )
done

for view in db/views/vw_ai_quanly.sql db/views/vw_ai_thungan.sql db/views/vw_ai_kho.sql; do
  mysql_root restaurant_integration < "$view"
done

# These are public fixture credentials for an isolated CI service, never production secrets.
mysql_root <<'SQL'
CREATE USER IF NOT EXISTS 'ci_ai_manager'@'%' IDENTIFIED BY 'ci-manager-pass';
CREATE USER IF NOT EXISTS 'ci_ai_cashier'@'%' IDENTIFIED BY 'ci-cashier-pass';
CREATE USER IF NOT EXISTS 'ci_ai_warehouse'@'%' IDENTIFIED BY 'ci-warehouse-pass';
ALTER USER 'ci_ai_manager'@'%' IDENTIFIED BY 'ci-manager-pass';
ALTER USER 'ci_ai_cashier'@'%' IDENTIFIED BY 'ci-cashier-pass';
ALTER USER 'ci_ai_warehouse'@'%' IDENTIFIED BY 'ci-warehouse-pass';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'ci_ai_manager'@'%';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'ci_ai_cashier'@'%';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'ci_ai_warehouse'@'%';
GRANT SELECT ON restaurant_integration.vw_ai_quanly TO 'ci_ai_manager'@'%';
GRANT SELECT ON restaurant_integration.vw_ai_thungan TO 'ci_ai_cashier'@'%';
GRANT SELECT ON restaurant_integration.vw_ai_kho TO 'ci_ai_warehouse'@'%';
SQL
