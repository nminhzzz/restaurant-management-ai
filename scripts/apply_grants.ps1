# PowerShell equivalent of apply_grants.sh for Windows
param()
$ErrorActionPreference = "Stop"
if (-not $env:AI_READONLY_PASSWORD_MANAGER) { throw "Set AI_READONLY_PASSWORD_MANAGER in your shell profile" }
if (-not $env:AI_READONLY_PASSWORD_CASHIER) { throw "Set AI_READONLY_PASSWORD_CASHIER in your shell profile" }
if (-not $env:AI_READONLY_PASSWORD_WAREHOUSE) { throw "Set AI_READONLY_PASSWORD_WAREHOUSE in your shell profile" }
$rootPwd = if ($env:MYSQL_ROOT_PASSWORD) { $env:MYSQL_ROOT_PASSWORD } else { "restaurant-root" }

foreach ($view in @("db/views/vw_ai_quanly.sql","db/views/vw_ai_thungan.sql","db/views/vw_ai_kho.sql")) {
  Get-Content $view | docker compose exec -T db mysql -uroot -p"$rootPwd" restaurant
}

$t = Get-Content db/views/grants.sql.template -Raw
$t = $t.Replace("__AI_READONLY_PASSWORD_MANAGER__", $env:AI_READONLY_PASSWORD_MANAGER)
$t = $t.Replace("__AI_READONLY_PASSWORD_CASHIER__", $env:AI_READONLY_PASSWORD_CASHIER)
$t = $t.Replace("__AI_READONLY_PASSWORD_WAREHOUSE__", $env:AI_READONLY_PASSWORD_WAREHOUSE)
$t | docker compose exec -T db mysql -uroot -p"$rootPwd" restaurant
