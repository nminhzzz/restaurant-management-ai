# Views và tài khoản chỉ-đọc (NFR-06, NFR-12)

Ba view `vw_ai_*` là ranh giới dữ liệu của trợ lý AI — mỗi vai trò chỉ thấy view của mình.
Tài khoản CSDL chỉ-đọc tương ứng chỉ được `GRANT SELECT` trên đúng view đó.

## Áp dụng

### macOS / Linux
```bash
export AI_READONLY_PASSWORD_MANAGER=...
export AI_READONLY_PASSWORD_CASHIER=...
export AI_READONLY_PASSWORD_WAREHOUSE=...
./scripts/apply_grants.sh
```

### Windows (PowerShell)
```powershell
$env:AI_READONLY_PASSWORD_MANAGER="..."
$env:AI_READONLY_PASSWORD_CASHIER="..."
$env:AI_READONLY_PASSWORD_WAREHOUSE="..."
powershell -ExecutionPolicy Bypass -File scripts/apply_grants.ps1
```

Mật khẩu không được commit — `grants.sql.template` chỉ chứa placeholder.

Điền cùng giá trị vào `AI_READONLY_URL_*` trong `.env` để API đăng nhập bằng các tài khoản này.
