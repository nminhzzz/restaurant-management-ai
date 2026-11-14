# Tổng hợp đánh giá: `eval-results-2026-11-13-graded.json`
## Theo cấu hình
| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 240 | 82.9% | 66.7% | 25.4% | 12.1% | 0.0% | 3.83 | 4.18 | 6.21 | 5392 | 341 | 0.0052 | 88.3% |
| B | 240 | 82.5% | 67.9% | 27.9% | 9.6% | 0.0% | 3.76 | 4.06 | 6.17 | 5959 | 353 | 0.0053 | 91.7% |
| C | 240 | 65.8% | 55.4% | 19.6% | 30.0% | 0.0% | 4.58 | 5.03 | 6.79 | 4283 | 336 | 0.0055 | 69.6% |

Tổng chi phí ghi nhận: 3.83 USD (thiếu ở các lượt usage chưa đủ).

## Theo vai trò

### Cấu hình A

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 80.6% | 65.6% | 24.4% | 16.1% | 0.0% | 4.02 | 4.48 | 6.46 | 5898 | 347 | 0.0051 | 84.4% |
| Thu ngân | 30 | 90.0% | 90.0% | 6.7% | 0.0% | 0.0% | 3.07 | 1.95 | 6.00 | 3246 | 291 | 0.0055 | 100.0% |
| Bếp | 30 | 90.0% | 50.0% | 50.0% | 0.0% | 0.0% | 3.42 | 4.00 | 4.89 | 4500 | 350 | 0.0051 | 100.0% |

### Cấu hình B

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 78.9% | 66.1% | 27.8% | 12.8% | 0.0% | 3.97 | 4.27 | 6.40 | 6614 | 363 | 0.0055 | 88.9% |
| Thu ngân | 30 | 100.0% | 100.0% | 10.0% | 0.0% | 0.0% | 2.88 | 2.02 | 5.28 | 3378 | 279 | 0.0048 | 100.0% |
| Bếp | 30 | 86.7% | 46.7% | 46.7% | 0.0% | 0.0% | 3.43 | 3.75 | 5.80 | 4609 | 364 | 0.0050 | 100.0% |

### Cấu hình C

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 59.4% | 53.3% | 19.4% | 37.2% | 0.0% | 4.76 | 5.04 | 6.86 | 4529 | 319 | 0.0053 | 62.2% |
| Thu ngân | 30 | 96.7% | 96.7% | 13.3% | 0.0% | 0.0% | 3.59 | 2.57 | 5.99 | 3378 | 378 | 0.0063 | 100.0% |
| Bếp | 30 | 73.3% | 26.7% | 26.7% | 16.7% | 0.0% | 4.48 | 4.32 | 7.17 | 3713 | 397 | 0.0055 | 83.3% |

## Theo mức khó

### Cấu hình A

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 90.0% | 86.7% | 27.8% | 1.1% | 0.0% | 2.39 | 1.95 | 4.69 | 5391 | 176 | 0.0055 | 98.9% |
| Trung bình | 90 | 86.7% | 70.0% | 25.6% | 10.0% | 0.0% | 4.42 | 4.37 | 5.56 | 5498 | 439 | 0.0047 | 90.0% |
| Khó | 60 | 66.7% | 31.7% | 21.7% | 31.7% | 0.0% | 5.08 | 5.03 | 6.93 | 5233 | 441 | 0.0053 | 70.0% |

### Cấu hình B

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 88.9% | 85.6% | 28.9% | 1.1% | 0.0% | 2.31 | 1.89 | 4.50 | 5651 | 168 | 0.0052 | 98.9% |
| Trung bình | 90 | 87.8% | 68.9% | 30.0% | 5.6% | 0.0% | 4.32 | 4.26 | 6.38 | 6073 | 463 | 0.0050 | 94.4% |
| Khó | 60 | 65.0% | 40.0% | 23.3% | 28.3% | 0.0% | 5.10 | 5.05 | 6.69 | 6250 | 465 | 0.0060 | 76.7% |

### Cấu hình C

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 83.3% | 76.7% | 18.9% | 5.6% | 0.0% | 3.31 | 2.93 | 5.89 | 5383 | 287 | 0.0065 | 94.4% |
| Trung bình | 90 | 72.2% | 60.0% | 25.6% | 27.8% | 0.0% | 5.28 | 5.14 | 6.79 | 4512 | 462 | 0.0060 | 72.2% |
| Khó | 60 | 30.0% | 16.7% | 11.7% | 70.0% | 0.0% | 5.43 | 5.04 | 7.19 | 2290 | 221 | 0.0032 | 28.3% |

## Các lượt lệch đáp án (không đạt nới lỏng)

### Cấu hình A: 41 lượt

**Q010** lần 2 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q014** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q022** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q022** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q022** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q030** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(ThanhTienMon), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(ThanhTienMon), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(h.TongTien), 0) / 30, 2) AS DoanhThuTrungBinhMoiNgay FROM vw_ai_quanly_hoadon AS h WHERE h.LoaiBanGhi = 'HOA_DON' AND h.BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q034** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q055** lần 2 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q055** lần 3 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 1 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon FROM vw_ai_quanly_ton AS t WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(t2.SoLuongTon) FROM vw_ai_quanly_ton AS t2 WHERE t2.LoaiBanGhi = 'TON_KHO') AND EXISTS(SELECT 1 FROM vw_ai_quanly_xuat AS x WHERE x.MaNguyenLieu = t.MaNguyenLieu AND x.BusinessDate BETWEEN '2026-09-24' AND '2026-10-23') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q060** lần 3 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q062** lần 1 · Thu ngân · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT COALESCE(SUM(SoTien), 0) AS TongTienThu FROM vw_ai_thungan_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q062** lần 2 · Thu ngân · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT COALESCE(SUM(SoTien), 0) AS TongTienThu FROM vw_ai_thungan_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q062** lần 3 · Thu ngân · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT COALESCE(SUM(SoTien), 0) AS TongTienThu FROM vw_ai_thungan_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q073** lần 3 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

### Cấu hình B: 42 lượt

**Q010** lần 3 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q014** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q022** lần 3 · Quản lý · Trung bình · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q030** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(ThanhTienMon) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(ThanhTienMon) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(TongTien) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_hoadon WHERE LoaiBanGhi = 'HOA_DON' AND BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q034** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT TenNguyenLieu, DonViTinh, AVG(DonGiaBinhQuan) AS GiaVonBinhQuanThangTruoc FROM vw_ai_quanly_giavon WHERE TenNguyenLieu LIKE '%Gạo%' AND NOT DonGiaBinhQuan IS NULL AND ThoiDiemHieuLuc >= '2026-09-01' AND ThoiDiemHieuLuc < '2026-10-01' GROUP BY MaNguyenLieu, TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT TenNguyenLieu, DonViTinh, AVG(DonGiaBinhQuan) AS GiaVonBinhQuanThangTruoc FROM vw_ai_quanly_giavon WHERE TenNguyenLieu = 'Gạo' AND NOT DonGiaBinhQuan IS NULL AND ThoiDiemHieuLuc >= '2026-09-01' AND ThoiDiemHieuLuc < '2026-10-01' GROUP BY TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 3 · Quản lý · Trung bình · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 1 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuTrongTuanSo, CASE DAYOFWEEK(BusinessDate) WHEN 1 THEN 'Chủ nhật' WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' ELSE 'Thứ Bảy' END AS ThuTrongTuan, SUM(TongTien) AS DoanhThu FROM vw_ai_quanly_hoadon WHERE LoaiBanGhi = 'HOA_DON' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY ThuTrongTuanSo LIMIT 500
```

**Q054** lần 2 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 1 THEN 'Chủ nhật' WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' ELSE 'Thứ Bảy' END AS ThuTrongTuan, SUM(ThanhTienMon) AS DoanhThu FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY ThuSo LIMIT 500
```

**Q054** lần 3 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 1 THEN 'Chủ nhật' WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' ELSE 'Thứ Bảy' END AS Thu, SUM(ThanhTienMon) AS DoanhThu FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY ThuSo LIMIT 500
```

**Q055** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END AS KyBaoCao, SUM(TongTien) AS DoanhThu FROM vw_ai_quanly_hoadon WHERE LoaiBanGhi = 'HOA_DON' AND BusinessDate BETWEEN '2026-09-01' AND '2026-10-23' GROUP BY CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END ORDER BY MIN(BusinessDate) LIMIT 500
```

**Q055** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT CASE WHEN BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' THEN 'Tháng này' ELSE 'Tháng trước' END AS Ky, SUM(TongTien) AS DoanhThu FROM vw_ai_quanly_hoadon WHERE LoaiBanGhi = 'HOA_DON' AND BusinessDate BETWEEN '2026-09-01' AND '2026-10-23' GROUP BY CASE WHEN BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' THEN 'Tháng này' ELSE 'Tháng trước' END ORDER BY Ky LIMIT 500
```

**Q055** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END AS Ky, SUM(ThanhTienMon) AS DoanhThu FROM vw_ai_quanly_dongmon WHERE LoaiBanGhi = 'DONG_MON' AND TrangThaiOrder = 'Đã thanh toán' AND BusinessDate BETWEEN '2026-09-01' AND '2026-10-23' GROUP BY CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END ORDER BY Ky LIMIT 500
```

**Q059** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 1 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon FROM vw_ai_quanly_ton AS t WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(t2.SoLuongTon) FROM vw_ai_quanly_ton AS t2 WHERE t2.LoaiBanGhi = 'TON_KHO') AND t.MaNguyenLieu IN (SELECT x.MaNguyenLieu FROM vw_ai_quanly_xuat AS x WHERE x.BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q060** lần 3 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 3 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q076** lần 2 · Bếp · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT BusinessDate, TenNguyenLieu, DonViTinh, SUM(SoLuongNhap) AS TongSoLuongNhap FROM vw_ai_kho_nhap WHERE BusinessDate >= '2026-10-01' AND BusinessDate <= '2026-10-23' GROUP BY BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh ORDER BY BusinessDate, TenNguyenLieu LIMIT 500
```

### Cấu hình C: 82 lượt

**Q003** lần 3 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q010** lần 1 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q010** lần 2 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q011** lần 2 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q012** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, SoLuongNhap, TenNhaCungCap, MaPhieuNhap, BusinessDate FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q012** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, BusinessDate, MaPhieuNhap, TenNhaCungCap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q012** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, SoLuongNhap, TenNhaCungCap, MaPhieuNhap, BusinessDate FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q013** lần 3 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q014** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoLuongNhap * DonGiaNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q021** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q021** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q022** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q022** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q022** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q023** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q025** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q025** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q028** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q030** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q030** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q030** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q034** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q039** lần 3 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q040** lần 1 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q040** lần 2 · Quản lý · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q041** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q041** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q041** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q042** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q042** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q043** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q043** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q043** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q044** lần 1 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q046** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q047** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q047** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q047** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q048** lần 2 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q049** lần 1 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q049** lần 3 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q050** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q050** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q051** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q052** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q054** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q055** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q055** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q055** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q057** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q058** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q058** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q058** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q059** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 1 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 2 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 3 · Quản lý · Khó · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q062** lần 1 · Thu ngân · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT COALESCE(SUM(SoTien), 0) AS TongTienThu FROM vw_ai_thungan_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 3 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q076** lần 1 · Bếp · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q076** lần 2 · Bếp · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q076** lần 3 · Bếp · Trung bình · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q080** lần 1 · Bếp · Trung bình · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q080** lần 3 · Bếp · Trung bình · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```
