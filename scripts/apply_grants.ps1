# PowerShell equivalent of apply_grants.sh for Windows
param()
$ErrorActionPreference = "Stop"
# Windows PowerShell 5.1 pipes ASCII by default, which would corrupt the Vietnamese view literals.
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if (-not $env:AI_READONLY_PASSWORD_MANAGER) { throw "Set AI_READONLY_PASSWORD_MANAGER in your shell profile" }
if (-not $env:AI_READONLY_PASSWORD_CASHIER) { throw "Set AI_READONLY_PASSWORD_CASHIER in your shell profile" }
if (-not $env:AI_READONLY_PASSWORD_WAREHOUSE) { throw "Set AI_READONLY_PASSWORD_WAREHOUSE in your shell profile" }
$rootPwd = if ($env:MYSQL_ROOT_PASSWORD) { $env:MYSQL_ROOT_PASSWORD } else { "restaurant-root" }
# One array element per argument: Windows PowerShell 5.1 splits a quoted value with spaces inside
# `--init-command="..."` into several arguments when it is written inline.
$mysqlArgs = @("-uroot", "-p$rootPwd", "--default-character-set=utf8mb4",
  "--init-command=SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci", "restaurant")

foreach ($view in @("db/views/vw_ai_quanly.sql","db/views/vw_ai_thungan.sql","db/views/vw_ai_kho.sql")) {
  Get-Content $view -Encoding utf8 | docker compose exec -T db mysql @mysqlArgs
}

$t = Get-Content db/views/grants.sql.template -Raw -Encoding utf8
$t = $t.Replace("__AI_READONLY_PASSWORD_MANAGER__", $env:AI_READONLY_PASSWORD_MANAGER)
$t = $t.Replace("__AI_READONLY_PASSWORD_CASHIER__", $env:AI_READONLY_PASSWORD_CASHIER)
$t = $t.Replace("__AI_READONLY_PASSWORD_WAREHOUSE__", $env:AI_READONLY_PASSWORD_WAREHOUSE)
$t | docker compose exec -T db mysql @mysqlArgs
