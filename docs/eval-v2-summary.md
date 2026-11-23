# Tổng hợp đánh giá: `eval-v2-results-graded.json`
## Theo cấu hình
| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 240 | 87.9% | 67.9% | 58.8% | 2.9% | 0.0% | 4.06 | 4.09 | 7.76 | 8082 | 410 | 0.0064 | 100.0% |
| B | 240 | 89.2% | 73.3% | 56.2% | 1.7% | 0.0% | 3.97 | 4.14 | 7.20 | 8135 | 406 | 0.0061 | 99.6% |
| C | 240 | 85.8% | 63.7% | 53.8% | 5.4% | 0.0% | 5.96 | 5.60 | 10.69 | 8270 | 622 | 0.0102 | 98.3% |

Tổng chi phí ghi nhận: 5.44 USD (thiếu ở các lượt usage chưa đủ).

## Theo vai trò

### Cấu hình A

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 85.6% | 66.1% | 58.3% | 3.9% | 0.0% | 4.28 | 4.20 | 7.86 | 9275 | 439 | 0.0066 | 100.0% |
| Thu ngân | 30 | 100.0% | 100.0% | 73.3% | 0.0% | 0.0% | 3.17 | 2.40 | 5.01 | 3774 | 279 | 0.0056 | 100.0% |
| Bếp | 30 | 90.0% | 46.7% | 46.7% | 0.0% | 0.0% | 3.62 | 3.94 | 5.87 | 5233 | 365 | 0.0056 | 100.0% |

### Cấu hình B

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 86.7% | 72.2% | 55.6% | 2.2% | 0.0% | 4.17 | 4.33 | 7.33 | 9309 | 434 | 0.0064 | 99.4% |
| Thu ngân | 30 | 100.0% | 100.0% | 70.0% | 0.0% | 0.0% | 3.03 | 2.21 | 5.83 | 3905 | 270 | 0.0050 | 100.0% |
| Bếp | 30 | 93.3% | 53.3% | 46.7% | 0.0% | 0.0% | 3.71 | 3.97 | 6.33 | 5320 | 377 | 0.0055 | 100.0% |

### Cấu hình C

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Quản lý | 180 | 84.4% | 65.0% | 56.7% | 7.2% | 0.0% | 6.38 | 5.95 | 10.93 | 9446 | 661 | 0.0110 | 97.8% |
| Thu ngân | 30 | 100.0% | 100.0% | 70.0% | 0.0% | 0.0% | 4.38 | 3.11 | 8.26 | 3909 | 439 | 0.0078 | 100.0% |
| Bếp | 30 | 80.0% | 20.0% | 20.0% | 0.0% | 0.0% | 5.05 | 5.26 | 7.40 | 5575 | 571 | 0.0077 | 100.0% |

## Theo mức khó

### Cấu hình A

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 90.0% | 86.7% | 86.7% | 0.0% | 0.0% | 2.56 | 2.10 | 5.11 | 6840 | 177 | 0.0060 | 100.0% |
| Trung bình | 90 | 87.8% | 71.1% | 48.9% | 4.4% | 0.0% | 4.59 | 4.26 | 10.15 | 8161 | 476 | 0.0055 | 100.0% |
| Khó | 60 | 85.0% | 35.0% | 31.7% | 5.0% | 0.0% | 5.52 | 5.29 | 7.86 | 9825 | 659 | 0.0082 | 100.0% |

### Cấu hình B

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 88.9% | 85.6% | 83.3% | 0.0% | 0.0% | 2.57 | 2.07 | 5.77 | 7113 | 187 | 0.0058 | 100.0% |
| Trung bình | 90 | 93.3% | 80.0% | 45.6% | 0.0% | 0.0% | 4.39 | 4.28 | 6.33 | 7934 | 484 | 0.0052 | 100.0% |
| Khó | 60 | 83.3% | 45.0% | 31.7% | 6.7% | 0.0% | 5.43 | 4.99 | 8.02 | 9970 | 618 | 0.0078 | 98.3% |

### Cấu hình C

| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dễ | 90 | 91.1% | 83.3% | 82.2% | 1.1% | 0.0% | 3.84 | 3.13 | 7.45 | 7073 | 355 | 0.0079 | 98.9% |
| Trung bình | 90 | 80.0% | 64.4% | 41.1% | 6.7% | 0.0% | 6.51 | 5.90 | 15.99 | 8497 | 694 | 0.0101 | 100.0% |
| Khó | 60 | 86.7% | 33.3% | 30.0% | 10.0% | 0.0% | 8.32 | 7.44 | 10.86 | 9727 | 916 | 0.0139 | 95.0% |

## Các lượt lệch đáp án (không đạt nới lỏng)

### Cấu hình A: 29 lượt

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

**Q019** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q022** lần 1 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, SUM(d.DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan WHERE d.BusinessDate >= '2026-10-01' AND d.BusinessDate <= '2026-10-23' AND NOT d.MaBan IS NULL GROUP BY d.MaBan, b.TenBan ORDER BY DoanhThu DESC LIMIT 5
```

**Q022** lần 2 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, SUM(d.DoanhThu) AS TongDoanhThu FROM vw_ai_quanly_doanhthu AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan WHERE d.BusinessDate >= '2026-10-01' AND d.BusinessDate <= '2026-10-23' AND NOT d.MaBan IS NULL GROUP BY d.MaBan, b.TenBan ORDER BY TongDoanhThu DESC LIMIT 5
```

**Q022** lần 3 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, SUM(d.DoanhThu) AS TongDoanhThu FROM vw_ai_quanly_doanhthu AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan WHERE d.BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT d.MaBan IS NULL GROUP BY d.MaBan, b.TenBan ORDER BY TongDoanhThu DESC LIMIT 5
```

**Q030** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DoanhThu) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DoanhThu) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DoanhThu) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q034** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.; Lỗi thực thi: OperationalError

```sql
SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '6' DAY) AND '2026-10-23' AND NOT MaHoaDon IS NULL GROUP BY MaBan ORDER BY DoanhThu DESC LIMIT 500
```

**Q034** lần 3 · Quản lý · Trung bình · lỗi · Kết quả khác SQL chuẩn.; Lỗi thực thi: OperationalError

```sql
SELECT b.MaBan, b.TenBan, COALESCE(d.TongDoanhThu, 0) AS DoanhThu FROM vw_ai_quanly_ban AS b LEFT JOIN (SELECT MaBan, SUM(DoanhThu) AS TongDoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '6' DAY) AND '2026-10-23' GROUP BY MaBan) AS d ON d.MaBan = b.MaBan ORDER BY DoanhThu DESC LIMIT 500
```

**Q039** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate >= '2026-09-01' AND BusinessDate < '2026-10-01' GROUP BY MaNguyenLieu, TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate >= '2026-09-01' AND BusinessDate < '2026-10-01' GROUP BY MaNguyenLieu, TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate >= '2026-09-01' AND BusinessDate < '2026-10-01' GROUP BY MaNguyenLieu, TenNguyenLieu LIMIT 500
```

**Q046** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS rk FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE rk = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q046** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS rk FROM vw_ai_quanly_doanhthu WHERE BusinessDate >= '2026-10-01' AND BusinessDate <= '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE rk = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q046** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS rk FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE rk = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q054** lần 1 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' WHEN 7 THEN 'Thứ Bảy' ELSE 'Chủ nhật' END AS ThuTrongTuan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate >= '2026-10-01' AND BusinessDate <= '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY CASE WHEN DAYOFWEEK(BusinessDate) = 1 THEN 8 ELSE DAYOFWEEK(BusinessDate) END LIMIT 500
```

**Q054** lần 2 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' WHEN 7 THEN 'Thứ Bảy' ELSE 'Chủ nhật' END AS ThuTrongTuan, SUM(DoanhThu) AS TongDoanhThu, COUNT(DISTINCT MaHoaDon) AS SoHoaDon FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY CASE WHEN DAYOFWEEK(BusinessDate) = 1 THEN 8 ELSE DAYOFWEEK(BusinessDate) END LIMIT 500
```

**Q054** lần 3 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' WHEN 7 THEN 'Thứ Bảy' ELSE 'Chủ nhật' END AS ThuTrongTuan, SUM(DoanhThu) AS DoanhThu, COUNT(DISTINCT MaHoaDon) AS SoHoaDon FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY CASE WHEN DAYOFWEEK(BusinessDate) = 1 THEN 8 ELSE DAYOFWEEK(BusinessDate) END LIMIT 7
```

**Q060** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon, x.TongXuatThuCong FROM vw_ai_quanly_ton AS t JOIN (SELECT MaNguyenLieu, SUM(SoLuongXuatThuCong) AS TongXuatThuCong FROM vw_ai_quanly_xuatnhapngay WHERE BusinessDate BETWEEN '2026-09-24' AND '2026-10-23' GROUP BY MaNguyenLieu HAVING SUM(SoLuongXuatThuCong) > 0) AS x ON x.MaNguyenLieu = t.MaNguyenLieu WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(SoLuongTon) FROM vw_ai_quanly_ton WHERE LoaiBanGhi = 'TON_KHO') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q060** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon, x.TongXuatThuCong FROM vw_ai_quanly_ton AS t JOIN (SELECT MaNguyenLieu, SUM(SoLuongXuatThuCong) AS TongXuatThuCong FROM vw_ai_quanly_xuatnhapngay WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' GROUP BY MaNguyenLieu HAVING SUM(SoLuongXuatThuCong) > 0) AS x ON x.MaNguyenLieu = t.MaNguyenLieu WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(SoLuongTon) FROM vw_ai_quanly_ton WHERE LoaiBanGhi = 'TON_KHO') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q060** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon, x.TongXuatThuCong FROM vw_ai_quanly_ton AS t JOIN (SELECT MaNguyenLieu, SUM(SoLuongXuatThuCong) AS TongXuatThuCong FROM vw_ai_quanly_xuatnhapngay WHERE BusinessDate BETWEEN '2026-09-24' AND '2026-10-23' GROUP BY MaNguyenLieu HAVING SUM(SoLuongXuatThuCong) <> 0) AS x ON x.MaNguyenLieu = t.MaNguyenLieu WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(SoLuongTon) FROM vw_ai_quanly_ton WHERE LoaiBanGhi = 'TON_KHO') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

**Q073** lần 3 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' LIMIT 500
```

### Cấu hình B: 26 lượt

**Q012** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, TenNhaCungCap, BusinessDate, MaPhieuNhap, DonGiaNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q012** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, TenNhaCungCap, BusinessDate, MaPhieuNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q014** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoLuongNhap * DonGiaNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoLuongNhap * DonGiaNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q014** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DonGiaNhap * SoLuongNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q019** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoTien) AS TongTienDaThu FROM vw_ai_quanly_thanhtoan WHERE LoaiBanGhi = 'THANH_TOAN' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q030** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(DoanhThu) / 30 AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(DoanhThu), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(DoanhThu), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q039** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY TenNguyenLieu LIMIT 500
```

**Q039** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY TenNguyenLieu LIMIT 500
```

**Q039** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY TenNguyenLieu LIMIT 500
```

**Q046** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS XepHang FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE XepHang = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q046** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS XepHang FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE XepHang = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q046** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaBan, BusinessDate, DoanhThuNgay FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS XepHang FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t WHERE XepHang = 1 ORDER BY MaBan, BusinessDate LIMIT 500
```

**Q054** lần 1 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 1 THEN 'Chủ nhật' WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' WHEN 7 THEN 'Thứ Bảy' END AS ThuTrongTuan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY ThuSo LIMIT 500
```

**Q054** lần 2 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuSo, CASE DAYOFWEEK(BusinessDate) WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' WHEN 7 THEN 'Thứ Bảy' ELSE 'Chủ nhật' END AS ThuTrongTuan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY CASE WHEN DAYOFWEEK(BusinessDate) = 1 THEN 8 ELSE DAYOFWEEK(BusinessDate) END LIMIT 500
```

**Q054** lần 3 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT DAYOFWEEK(BusinessDate) AS ThuTrongTuanSo, CASE DAYOFWEEK(BusinessDate) WHEN 1 THEN 'Chủ nhật' WHEN 2 THEN 'Thứ Hai' WHEN 3 THEN 'Thứ Ba' WHEN 4 THEN 'Thứ Tư' WHEN 5 THEN 'Thứ Năm' WHEN 6 THEN 'Thứ Sáu' ELSE 'Thứ Bảy' END AS ThuTrongTuan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY DAYOFWEEK(BusinessDate) ORDER BY ThuTrongTuanSo LIMIT 500
```

**Q055** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END AS Ky, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-09-01' AND '2026-10-23' GROUP BY CASE WHEN BusinessDate >= '2026-10-01' THEN 'Tháng này' ELSE 'Tháng trước' END ORDER BY Ky LIMIT 500
```

**Q060** lần 1 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon, x.TongXuatThuCong FROM vw_ai_quanly_ton AS t JOIN (SELECT MaNguyenLieu, SUM(SoLuongXuatThuCong) AS TongXuatThuCong FROM vw_ai_quanly_xuatnhapngay WHERE BusinessDate BETWEEN '2026-09-24' AND '2026-10-23' GROUP BY MaNguyenLieu HAVING SUM(SoLuongXuatThuCong) > 0) AS x ON x.MaNguyenLieu = t.MaNguyenLieu WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(SoLuongTon) FROM vw_ai_quanly_ton WHERE LoaiBanGhi = 'TON_KHO') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q060** lần 2 · Quản lý · Khó · lỗi · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q060** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.; Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
SELECT t.MaNguyenLieu, t.TenNguyenLieu, t.DonViTinh, t.SoLuongTon, x.TongXuatThuCong FROM vw_ai_quanly_ton AS t JOIN (SELECT MaNguyenLieu, SUM(SoLuongXuatThuCong) AS TongXuatThuCong FROM vw_ai_quanly_xuatnhapngay WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' GROUP BY MaNguyenLieu HAVING SUM(SoLuongXuatThuCong) > 0) AS x ON x.MaNguyenLieu = t.MaNguyenLieu WHERE t.LoaiBanGhi = 'TON_KHO' AND t.SoLuongTon < (SELECT AVG(SoLuongTon) FROM vw_ai_quanly_ton WHERE LoaiBanGhi = 'TON_KHO') ORDER BY t.SoLuongTon ASC LIMIT 500
```

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

### Cấu hình C: 34 lượt

**Q010** lần 1 · Quản lý · Dễ · lỗi · Lỗi gọi LLM hoặc timeout: TimeoutError

```sql
-- (không sinh SQL)
```

**Q012** lần 1 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, BusinessDate, MaPhieuNhap, TenNhaCungCap, DonGiaNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q012** lần 2 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, BusinessDate, MaPhieuNhap, TenNhaCungCap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q012** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, DonGiaNhap, BusinessDate, MaPhieuNhap, TenNhaCungCap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND TenNguyenLieu LIKE '%Thịt bò%' AND NOT DonGiaNhap IS NULL ORDER BY BusinessDate DESC, MaPhieuNhap DESC LIMIT 1
```

**Q014** lần 3 · Quản lý · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT SUM(SoLuongNhap * DonGiaNhap) AS TongTienNhap FROM vw_ai_quanly_nhap WHERE LoaiBanGhi = 'PHIEU_NHAP' AND BusinessDate = '2026-10-23' LIMIT 500
```

**Q022** lần 1 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, d.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan) AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan ORDER BY d.DoanhThu DESC LIMIT 5
```

**Q022** lần 2 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, d.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan) AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan ORDER BY d.DoanhThu DESC LIMIT 5
```

**Q022** lần 3 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT t.MaBan, b.TenBan, t.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan) AS t LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = t.MaBan ORDER BY t.DoanhThu DESC LIMIT 5
```

**Q030** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(DoanhThu), 0) / 30, 2) AS DoanhThuTrungBinhMoiNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(DoanhThu), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q030** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT ROUND(COALESCE(SUM(DoanhThu), 0) / 30, 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '29' DAY) AND '2026-10-23' LIMIT 500
```

**Q034** lần 1 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT dt.MaBan, b.TenBan, dt.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-17' AND '2026-10-23' GROUP BY MaBan) AS dt LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = dt.MaBan ORDER BY dt.DoanhThu DESC LIMIT 500
```

**Q034** lần 2 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, d.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN DATE_SUB('2026-10-23', INTERVAL '6' DAY) AND '2026-10-23' GROUP BY MaBan) AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan ORDER BY d.DoanhThu DESC LIMIT 500
```

**Q034** lần 3 · Quản lý · Trung bình · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT d.MaBan, b.TenBan, d.DoanhThu FROM (SELECT MaBan, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-17' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan) AS d LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = d.MaBan ORDER BY d.DoanhThu DESC LIMIT 500
```

**Q037** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT LyDoHuyOrder, COUNT(DISTINCT MaOrder) AS SoLan FROM vw_ai_quanly_order WHERE LoaiBanGhi = 'ORDER' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT LyDoHuyOrder IS NULL AND TRIM(LyDoHuyOrder) <> '' GROUP BY LyDoHuyOrder ORDER BY SoLan DESC LIMIT 500
```

**Q037** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT LyDoHuyOrder, COUNT(DISTINCT MaOrder) AS SoLan FROM vw_ai_quanly_order WHERE LoaiBanGhi = 'ORDER' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT LyDoHuyOrder IS NULL AND TRIM(LyDoHuyOrder) <> '' GROUP BY LyDoHuyOrder ORDER BY SoLan DESC LIMIT 500
```

**Q037** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT LyDoHuyOrder, COUNT(DISTINCT MaOrder) AS SoLan FROM vw_ai_quanly_order WHERE LoaiBanGhi = 'ORDER' AND NOT LyDoHuyOrder IS NULL AND LyDoHuyOrder <> '' AND BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY LyDoHuyOrder ORDER BY SoLan DESC LIMIT 500
```

**Q039** lần 1 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT MaNguyenLieu, TenNguyenLieu, DonViTinh, SUM(GiaVon) AS TongGiaVon, SUM(SoLuongGiaVon) AS TongSoLuongGiaVon, ROUND(SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0), 2) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY MaNguyenLieu, TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 2 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0) AS GiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu = 'Gạo' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY TenNguyenLieu, DonViTinh LIMIT 500
```

**Q039** lần 3 · Quản lý · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SUM(GiaVon) AS TongGiaVon, SUM(SoLuongGiaVon) AS TongSoLuong, ROUND(SUM(GiaVon) / NULLIF(SUM(SoLuongGiaVon), 0), 2) AS DonGiaVonBinhQuan FROM vw_ai_quanly_xuatnhapngay WHERE TenNguyenLieu LIKE '%Gạo%' AND BusinessDate BETWEEN '2026-09-01' AND '2026-09-30' GROUP BY TenNguyenLieu, DonViTinh LIMIT 500
```

**Q046** lần 1 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT r.MaBan, b.TenBan, r.BusinessDate, r.DoanhThuNgay FROM (SELECT t.MaBan, t.BusinessDate, t.DoanhThuNgay, RANK() OVER (PARTITION BY t.MaBan ORDER BY t.DoanhThuNgay DESC) AS rk FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThuNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t) AS r LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = r.MaBan WHERE r.rk = 1 ORDER BY r.MaBan, r.BusinessDate LIMIT 500
```

**Q046** lần 2 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT t.MaBan, b.TenBan, t.BusinessDate, t.DoanhThu FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThu, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS XepHang FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS t LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = t.MaBan WHERE t.XepHang = 1 ORDER BY t.MaBan, t.BusinessDate LIMIT 500
```

**Q046** lần 3 · Quản lý · Khó · lỗi · Lỗi thực thi: OperationalError

```sql
SELECT x.MaBan, b.TenBan, x.BusinessDate, x.DoanhThu FROM (SELECT MaBan, BusinessDate, SUM(DoanhThu) AS DoanhThu, RANK() OVER (PARTITION BY MaBan ORDER BY SUM(DoanhThu) DESC) AS XepHang FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' AND NOT MaBan IS NULL GROUP BY MaBan, BusinessDate) AS x LEFT JOIN vw_ai_quanly_ban AS b ON b.MaBan = x.MaBan WHERE x.XepHang = 1 ORDER BY x.MaBan, x.BusinessDate LIMIT 500
```

**Q054** lần 2 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT WEEKDAY(BusinessDate) + 2 AS ThuSo, CASE WEEKDAY(BusinessDate) WHEN 0 THEN 'Thứ Hai' WHEN 1 THEN 'Thứ Ba' WHEN 2 THEN 'Thứ Tư' WHEN 3 THEN 'Thứ Năm' WHEN 4 THEN 'Thứ Sáu' WHEN 5 THEN 'Thứ Bảy' ELSE 'Chủ nhật' END AS ThuTrongTuan, COUNT(DISTINCT BusinessDate) AS SoNgay, COUNT(DISTINCT MaHoaDon) AS SoHoaDon, SUM(DoanhThu) AS DoanhThu, ROUND(SUM(DoanhThu) / COUNT(DISTINCT BusinessDate), 2) AS DoanhThuTrungBinhNgay FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY ThuSo, ThuTrongTuan ORDER BY ThuSo LIMIT 500
```

**Q054** lần 3 · Quản lý · Khó · sai · Kết quả khác SQL chuẩn.

```sql
SELECT WEEKDAY(BusinessDate) + 2 AS ThuSo, ELT(WEEKDAY(BusinessDate) + 1, 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ nhật') AS ThuTrongTuan, COUNT(DISTINCT BusinessDate) AS SoNgay, COUNT(DISTINCT MaHoaDon) AS SoHoaDon, SUM(DoanhThu) AS DoanhThu FROM vw_ai_quanly_doanhthu WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY ThuSo, ThuTrongTuan ORDER BY ThuSo LIMIT 500
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

**Q073** lần 1 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SoLuongTon, DonViTinh, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 2 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, DonViTinh, SoLuongTon, SoLuongGiu, SoLuongKhaDung, MucTonToiThieu, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q073** lần 3 · Bếp · Dễ · sai · Kết quả khác SQL chuẩn.

```sql
SELECT TenNguyenLieu, SoLuongTon, DonViTinh, SoLuongKhaDung, ThoiDiemTinh FROM vw_ai_kho_ton WHERE LoaiBanGhi = 'TON_KHO' AND TenNguyenLieu LIKE '%Thịt bò%' ORDER BY TenNguyenLieu LIMIT 500
```

**Q076** lần 1 · Bếp · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh, SUM(SoLuongNhap) AS TongSoLuongNhap, SUM(SoLuongHuyNhap) AS TongSoLuongHuyNhap FROM vw_ai_kho_xuatnhapngay WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh HAVING SUM(SoLuongNhap) <> 0 OR SUM(SoLuongHuyNhap) <> 0 ORDER BY BusinessDate, TenNguyenLieu LIMIT 500
```

**Q076** lần 2 · Bếp · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh, SUM(SoLuongNhap) AS SoLuongNhap FROM vw_ai_kho_xuatnhapngay WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh HAVING SUM(SoLuongNhap) > 0 ORDER BY BusinessDate, TenNguyenLieu LIMIT 500
```

**Q076** lần 3 · Bếp · Trung bình · sai · Kết quả khác SQL chuẩn.

```sql
SELECT BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh, SUM(SoLuongNhap) AS TongSoLuongNhap FROM vw_ai_kho_xuatnhapngay WHERE BusinessDate BETWEEN '2026-10-01' AND '2026-10-23' GROUP BY BusinessDate, MaNguyenLieu, TenNguyenLieu, DonViTinh HAVING SUM(SoLuongNhap) > 0 ORDER BY BusinessDate, TenNguyenLieu LIMIT 500
```
