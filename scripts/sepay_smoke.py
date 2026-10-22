#!/usr/bin/env python3
"""End-to-end smoke test for a real SePay/VietQR transfer.

Creates a one-dish order on a free table, starts a QR payment, then waits while you
pay it from a banking app. It uses the same HTTP endpoints as the cashier screen, so
a green run proves webhook (or the bank-listing fallback) really settles money.

The API must run with PAYMENT_GATEWAY=sepay and real SEPAY_* credentials, and SePay
must be able to reach POST /api/v1/sales/webhooks/sepay over HTTPS.

Usage:
    API_BASE_URL=https://api.example.vn \
    SMOKE_USERNAME=quanly SMOKE_PASSWORD=... \
    uv run --project apps/api python scripts/sepay_smoke.py

Options:
    --api-url      API root (default: API_BASE_URL or http://localhost:8000)
    --username     account (default: SMOKE_USERNAME)
    --password     password (default: SMOKE_PASSWORD)
    --table        table id to use (default: first free table)
    --dish         dish id to order (default: first listed dish)
    --timeout      seconds to wait for the money (default: 900)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-url", default=os.environ.get("API_BASE_URL", "http://localhost:8000")
    )
    parser.add_argument("--username", default=os.environ.get("SMOKE_USERNAME", ""))
    parser.add_argument("--password", default=os.environ.get("SMOKE_PASSWORD", ""))
    parser.add_argument("--table", type=int, default=None)
    parser.add_argument("--dish", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if not args.username or not args.password:
        fail("set --username/--password or SMOKE_USERNAME/SMOKE_PASSWORD")

    base = args.api_url.rstrip("/")
    api = f"{base}/api/v1"
    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{base}/health")
        health.raise_for_status()
        payment = health.json().get("payment") or {}
        if not payment.get("live"):
            fail(f"API is not in live SePay mode: {payment}")
        print(
            f"API live: gateway={payment['gateway']} bank={payment.get('bank_code')} "
            f"account={payment.get('bank_account')}"
        )

        token = client.post(
            f"{api}/settings/auth/login",
            json={"username": args.username, "password": args.password},
        )
        if token.status_code != 200:
            fail(f"login failed: {token.status_code} {token.text}")
        client.headers["Authorization"] = f"Bearer {token.json()['access_token']}"

        tables = client.get(f"{api}/catalog/tables").json()
        table = next(
            (t for t in tables if args.table is not None and t["MaBan"] == args.table),
            None,
        ) or next((t for t in tables if t.get("TrangThai") == "Trống"), None)
        if table is None:
            fail(
                f"no free table found (tables={[(t['MaBan'], t.get('TrangThai')) for t in tables]})"
            )

        dishes = client.get(f"{api}/catalog/dishes", params={"size": 200}).json()[
            "items"
        ]
        dish = next(
            (d for d in dishes if args.dish is not None and d["MaMon"] == args.dish),
            None,
        ) or next((d for d in dishes if d.get("TrangThai") == "Hoạt động"), None)
        if dish is None:
            fail(
                "no sellable dish found; pass --dish with a dish that has a recipe and stock"
            )

        order = client.post(
            f"{api}/sales/orders",
            json={
                "MaBan": table["MaBan"],
                "lines": [{"MaMon": dish["MaMon"], "SoLuong": 1}],
            },
        )
        if order.status_code != 201:
            fail(f"could not create order: {order.status_code} {order.text}")
        created = order.json()
        order_id = created["MaOrder"]
        print(
            f"Order {created.get('MaOrderHienThi') or order_id}: 1 x {dish.get('TenMon')}"
        )

        qr = client.post(f"{api}/sales/orders/{order_id}/pay/qr")
        if qr.status_code != 201:
            fail(f"could not start QR: {qr.status_code} {qr.text}")
        started = qr.json()
        payment_id = started["MaGiaoDich"]
        amount = started["SoTien"]
        print()
        print("=" * 68)
        print(
            f"Transfer exactly {amount} VND with content: {started.get('payment_code')}"
        )
        print(
            f"Bank: {started.get('bank_code')}  Account: {started.get('bank_account')}"
        )
        print(f"Account name: {started.get('account_name')}")
        if started.get("qr_image_url"):
            print(f"VietQR: {started['qr_image_url']}")
        print(f"Payment id: {payment_id}. Waiting up to {args.timeout}s ...")
        print("=" * 68)

        deadline = time.monotonic() + args.timeout
        status = started["TrangThai"]
        while time.monotonic() < deadline:
            time.sleep(3)
            rows = client.get(f"{api}/sales/orders/{order_id}/payments").json()["items"]
            current = next(
                (row for row in rows if row["MaGiaoDich"] == payment_id), None
            )
            if current is None:
                continue
            if current["TrangThai"] != status:
                status = current["TrangThai"]
                print(f"status: {status}")
            if status == "Thành công":
                invoice = client.get(f"{api}/sales/orders/{order_id}/invoice").json()
                print(
                    f"OK: paid. Invoice {invoice['SoHoaDon']} total {invoice['TongTien']}"
                )
                return
            if status in ("Hết hạn", "Chờ xác minh thanh toán"):
                # Exercise the bank-listing fallback the cashier uses after a missed webhook.
                client.post(f"{api}/sales/payments/{payment_id}/check")

        fail(f"no payment after {args.timeout}s (last status: {status})")


if __name__ == "__main__":
    main()
