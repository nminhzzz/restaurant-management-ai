# Kết quả kiểm thử hiệu năng (Phụ lục J) — 27/10/2026

Tài liệu ghi lại lần chạy thực tế kịch bản Phụ lục J của `docs/BaoCao_HeThongQuanLyNhaHang.md` (mục J.1–J.7)
trên API đã triển khai. Toàn bộ số liệu thô nằm ở `docs/testing/artifacts/2026-10-27-perf/`.

## 1. Tóm tắt

| Tiêu chí | Ngưỡng | Kết quả | Kết luận |
| --- | --- | --- | --- |
| NFR-01 — p95 từng thao tác nghiệp vụ, mỗi mức tải | ≤ 1 s | p95 gộp 3 lần lớn nhất 272 ms (`send`, 10 VU); p95 của một lần lặp đơn lẻ lớn nhất 604 ms (`hold`, 20 VU, lần 1) | **Đạt** theo tiêu chí p95, **kèm lỗi độ tin cậy ở 20 VU** (mục 6) |
| NFR-03 — p95 từng loại báo cáo | < 10 s | p95 gộp lớn nhất 41 ms (xếp hạng món) | **Đạt** (dư địa hơn 200 lần) |
| Kiểm tra bất biến sau chạy (J.7) | không vi phạm | 13/13 lượt `verify_perf` không có lỗi | **Đạt** |

Điểm cần lưu ý trung thực: ở 20 VU, lần lặp 1 và 2 xảy ra hiện tượng API đứng hình khoảng 30 giây
(cạn pool kết nối CSDL), gây 20 lỗi kỹ thuật trong cửa sổ đo của lần 1 (0,06–0,77 % tùy thao tác) và nhiều
lỗi hơn trong giai đoạn khởi động. Chúng không làm p95 vượt 1 s nhưng làm công cụ `load_business` trả mã thoát 1
cho lần chạy đó (công cụ coi mọi lỗi kỹ thuật là không đạt). Phân tích ở mục 6.

## 2. Môi trường

| Hạng mục | Giá trị |
| --- | --- |
| Máy | Mac16,8, Apple M4 Pro, 12 lõi (8 hiệu năng + 4 tiết kiệm), RAM 24 GiB |
| Hệ điều hành | macOS 27.0.1 (build 26A434) |
| Docker | OrbStack, Docker Engine 29.8.2; máy ảo 12 CPU, giới hạn bộ nhớ container ~11,7 GiB |
| CSDL | MySQL 8.4.11 trong container `restaurant-db`; `innodb_buffer_pool_size` = 128 MiB (mặc định), `max_connections` = 151, mức cô lập REPEATABLE-READ |
| CSDL thử | `perf_restaurant` (bộ ký tự utf8mb4, collation `utf8mb4_unicode_ci`, giống CSDL `restaurant`), tài khoản riêng `perf_app` chỉ có quyền trên `perf_restaurant.*` |
| API | FastAPI, Python 3.12.14, một tiến trình `uvicorn` (không `--reload`), cổng 8001, `PAYMENT_GATEWAY=simulator`, `AI_PROVIDER=fake`; pool kết nối mặc định của SQLAlchemy (5 + 10 tràn, chờ tối đa 30 s) |
| Máy phát tải | cùng máy với API và CSDL (không qua mạng), `httpx`, timeout 30 s |
| Commit | `a5dbec15196fd7eba46fb61f0043f228e0dbccea` (nhánh `feat/interpretation-facts`); thư mục `apps/api/src` và `scripts` không có thay đổi chưa commit ở mọi lần chạy (ghi trong `driver.log`) |

**Lưu ý về tải của máy chủ (quan trọng khi đọc số liệu).** Máy này được dùng chung với các tiến trình nặng khác
(chạy kiểm thử của các dự án khác, trình duyệt, v.v.) trong suốt thời gian đo. Tải trung bình 1 phút (`uptime`) dao
động từ khoảng 3,9 đến 25,7 trên 12 lõi; CPU rảnh có lúc xuống 0 % (xem `resources-*.csv`). Vì vậy các số đo là
**điều kiện thực tế trên máy dùng chung, không phải môi trường cô lập**; chênh lệch giữa các lần lặp (đặc biệt
10 VU lần 1, nơi tải máy trung bình 15,3 và đỉnh 25,7) một phần đến từ nhiễu này. Bộ đếm CSDL (`Threads_connected`,
`Innodb_row_lock_time`) là bộ đếm toàn instance MySQL, và container này còn chứa các CSDL khác của dự án
(không có hoạt động trong lúc đo, nhưng bộ đếm không tách riêng được).

## 3. Quy trình đã thực hiện

1. Container `restaurant-db` đang ở trạng thái dừng khi bắt đầu; đã khởi động lại bằng `docker start` (không tác động dữ liệu).
2. Tạo CSDL `perf_restaurant` và người dùng `perf_app` (mật khẩu sinh ngẫu nhiên, chỉ lưu ở tệp quyền 600 trong thư mục tạm); `GRANT ALL` chỉ trên `perf_restaurant.*`. CSDL `restaurant` (bản chốt đánh giá) không bị chạm tới.
3. `alembic upgrade head` lên `perf_restaurant` (revision `d23102300006`), `DATABASE_URL` chỉ đặt cho lệnh đó.
4. `scripts/seed_perf.py` với `seed=20261019`, `orders=20000`, `months=12`, `users=20`, mốc tham chiếu mặc định của công cụ `2026-10-19 12:00`. Chạy 22 phút 20 giây (13:14–13:36, giờ +07). Kết quả: 20.000 order (18.000 đã thanh toán, 1.000 hủy, 500 chờ xác minh, 500 đóng chưa thu được tiền), 40 món, 30 nguyên liệu, 20 bàn, 5 nhà cung cấp, 63.135 giao dịch kho, 30 lô, tổng doanh thu 3.739.234.000, checksum `84923db2…`. Tự kiểm tra của công cụ seed không báo lỗi.
5. Chụp bản sao bằng `mysqldump --single-transaction` (46 MB). Mỗi lần chạy phục hồi bằng cách nạp lại bản dump này (mất khoảng 8–14 giây). Việc phục hồi được chứng minh: sau mỗi lần phục hồi và lần chạy báo cáo, số bản ghi và checksum trở lại đúng bản gốc (`verify-rep-vu05-r*.slim.json`, `verify-snapshot.slim.json`).
6. Chạy thử nhanh (5 VU, khởi động 10 s, đo 30 s, cả phát tải nghiệp vụ và báo cáo) để kiểm tra đường ống; tuyến mặc định của `load.py` khớp API thật nên **không cần tệp `--api-map`**. Số liệu chạy thử không dùng trong kết quả.
7. Chạy chính thức bằng một tập lệnh điều khiển duy nhất (`driver.sh`), tuần tự, từ 13:42 đến 16:13: `load_business` ở 5, 10, 20 VU, mỗi mức 3 lần lặp, mỗi lần khởi động 120 s + đo 600 s; sau đó `load_reports` 5 VU, 3 lần lặp cùng thời lượng. Trước **mỗi** lần chạy: phục hồi bản sao, khởi động mới API (PID được ghi lại và chỉ tắt đúng PID đó), kiểm tra `/health`. Mỗi lần chạy dùng cùng `seed=20261019`.
8. Trong mỗi lần chạy, một vòng lấy mẫu ghi mỗi ~30 s: `uptime`, CPU rảnh toàn máy (`top`), CPU/RAM container CSDL (`docker stats`), `Threads_connected`, `Innodb_row_lock_time`, `Innodb_row_lock_waits`, CPU/RSS tiến trình API (`resources-*.csv`).
9. Sau **mỗi** lần chạy (trước khi phục hồi), chạy `scripts/verify_perf.py --baseline manifest.json`; kết quả đầy đủ (~12 MB mỗi tệp, gồm sổ cái) được rút gọn thành `verify-*.slim.json` (lỗi, số bản ghi, trạng thái order, doanh thu, checksum).
10. Kết thúc: phục hồi bản sao lần cuối, tắt API. API không còn chạy; cổng 8001 đã trống. `perf_restaurant` và người dùng `perf_app` được **giữ lại** trong container `restaurant-db`.

### Sai lệch so với đặc tả (khai báo đầy đủ)

- Mã nguồn thay đổi trong lúc chạy: một phiên làm việc khác trên cùng kho mã chuyển sang nhánh `feat/interpretation-facts` (13:13) và tạo hai commit (13:16 và 13:22, chỉ sửa `ai/pipeline/interpreter.py`, kiểm thử, script demo và tài liệu). Phần seed bắt đầu ở 13:14 trên mã tương đương `9edce21`; các lần đo đều chạy ở `a5dbec1`. Hai commit trên không chạm vào mô-đun bán hàng, kho, báo cáo nên không ảnh hưởng đường đo, nhưng đây là điểm khác với môi trường đóng băng hoàn toàn. Tệp `.env.example` đang có thay đổi chưa commit từ trước (ngoài phạm vi).
- Công cụ tính p95 chỉ trên các request thành công (`outcome=ok`); request bị lỗi kỹ thuật (timeout 30 s) không nằm trong p95 nhưng được đếm trong tỷ lệ lỗi. Mục 6 bổ sung p95 tính cả mẫu lỗi để đối chiếu.
- Chu trình tải chỉ gồm các thao tác nghiệp vụ trong J.3; không có thao tác thanh toán hay in phiếu bếp nên bộ giả lập thanh toán (đã bật) và máy in (không cấu hình) không nằm trong phép đo, đúng tinh thần "tách khỏi phép đo API".
- Thông lượng ghi trong bảng là số request thành công mỗi giây trong cửa sổ đo 600 s (đúng định nghĩa của công cụ). Vì mỗi VU nghỉ ngẫu nhiên 1–3 s giữa thao tác, thông lượng chủ yếu phản ánh số VU, không phải sức chứa tối đa của hệ thống.
- Số đo CPU/kết nối/thời gian khóa lấy mẫu ở chu kỳ ~30 s, mang tính tổng quan (không phải đo liên tục).
- Trạng thái cache: không có cache ứng dụng cho `reports/revenue` và `reports/dishes` (bộ nhớ đệm duy nhất của mô-đun báo cáo chỉ phục vụ `/reports/comparison`, không được gọi); API khởi động mới cho mỗi lần chạy nên mọi cache tiến trình đều rỗng ở đầu giai đoạn khởi động; bộ nhớ đệm trang InnoDB (128 MiB) là nguội ở đầu mỗi lần chạy và ấm dần trong 120 s khởi động.

## 4. Kết quả phát tải nghiệp vụ (NFR-01)

Quy ước: mẫu = số request trong cửa sổ đo (giai đoạn khởi động đã loại); p50/p95 tính trên request thành công;
thông lượng = request thành công/600 s; lỗi kỹ thuật là số (và tỷ lệ trên mẫu). Hàng đậm là **p95 gộp**:
trộn toàn bộ mẫu của 3 lần lặp rồi tính phân vị, không lấy trung bình các p95. Không có từ chối nghiệp vụ (HTTP 409)
nào ở bất kỳ mức tải nào.

### 4.1. 5 VU

| Thao tác | Lần | Mẫu | p50 (ms) | p95 (ms) | Thông lượng (req/s) | Lỗi kỹ thuật |
|---|---|---:|---:|---:|---:|---:|
| hold | 1 | 296 | 35 | 80 | 0,49 | 0 |
| hold | 2 | 297 | 29 | 63 | 0,49 | 0 |
| hold | 3 | 297 | 29 | 76 | 0,49 | 0 |
| **hold** | **gộp** | 890 | 30 | **74** | 1,48 | 0 (0,00 %) |
| adjust_hold | 1 | 293 | 36 | 77 | 0,49 | 0 |
| adjust_hold | 2 | 298 | 31 | 61 | 0,50 | 0 |
| adjust_hold | 3 | 295 | 29 | 77 | 0,49 | 0 |
| **adjust_hold** | **gộp** | 886 | 31 | **73** | 1,48 | 0 (0,00 %) |
| send | 1 | 294 | 64 | 143 | 0,49 | 0 |
| send | 2 | 296 | 53 | 111 | 0,49 | 0 |
| send | 3 | 293 | 54 | 135 | 0,49 | 0 |
| **send** | **gộp** | 883 | 56 | **132** | 1,47 | 0 (0,00 %) |
| read_order | 1 | 147 | 46 | 67 | 0,24 | 0 |
| read_order | 2 | 148 | 45 | 63 | 0,25 | 0 |
| read_order | 3 | 147 | 45 | 66 | 0,24 | 0 |
| **read_order** | **gộp** | 442 | 45 | **65** | 0,74 | 0 (0,00 %) |
| read_menu | 1 | 147 | 82 | 189 | 0,24 | 0 |
| read_menu | 2 | 147 | 67 | 148 | 0,24 | 0 |
| read_menu | 3 | 147 | 72 | 135 | 0,24 | 0 |
| **read_menu** | **gộp** | 441 | 74 | **158** | 0,73 | 0 (0,00 %) |
| catalog | 1 | 149 | 28 | 65 | 0,25 | 0 |
| catalog | 2 | 147 | 23 | 50 | 0,24 | 0 |
| catalog | 3 | 147 | 22 | 44 | 0,24 | 0 |
| **catalog** | **gộp** | 443 | 24 | **54** | 0,74 | 0 (0,00 %) |
| receipt | 1 | 150 | 32 | 82 | 0,25 | 0 |
| receipt | 2 | 147 | 25 | 44 | 0,24 | 0 |
| receipt | 3 | 147 | 25 | 53 | 0,24 | 0 |
| **receipt** | **gộp** | 444 | 27 | **61** | 0,74 | 0 (0,00 %) |

### 4.2. 10 VU

| Thao tác | Lần | Mẫu | p50 (ms) | p95 (ms) | Thông lượng (req/s) | Lỗi kỹ thuật |
|---|---|---:|---:|---:|---:|---:|
| hold | 1 | 572 | 41 | 418 | 0,95 | 0 |
| hold | 2 | 592 | 27 | 55 | 0,99 | 0 |
| hold | 3 | 579 | 27 | 105 | 0,96 | 0 |
| **hold** | **gộp** | 1743 | 30 | **200** | 2,90 | 0 (0,00 %) |
| adjust_hold | 1 | 571 | 43 | 356 | 0,95 | 0 |
| adjust_hold | 2 | 593 | 30 | 60 | 0,99 | 0 |
| adjust_hold | 3 | 582 | 30 | 167 | 0,97 | 0 |
| **adjust_hold** | **gộp** | 1746 | 33 | **211** | 2,91 | 0 (0,00 %) |
| send | 1 | 570 | 85 | 548 | 0,95 | 0 |
| send | 2 | 592 | 51 | 103 | 0,99 | 0 |
| send | 3 | 581 | 52 | 145 | 0,97 | 0 |
| **send** | **gộp** | 1743 | 57 | **272** | 2,90 | 0 (0,00 %) |
| read_order | 1 | 283 | 35 | 83 | 0,47 | 0 |
| read_order | 2 | 295 | 44 | 61 | 0,49 | 0 |
| read_order | 3 | 292 | 39 | 59 | 0,49 | 0 |
| **read_order** | **gộp** | 870 | 41 | **62** | 1,45 | 0 (0,00 %) |
| read_menu | 1 | 283 | 107 | 365 | 0,47 | 0 |
| read_menu | 2 | 293 | 66 | 125 | 0,49 | 0 |
| read_menu | 3 | 291 | 72 | 174 | 0,48 | 0 |
| **read_menu** | **gộp** | 867 | 78 | **252** | 1,45 | 0 (0,00 %) |
| catalog | 1 | 284 | 30 | 446 | 0,47 | 0 |
| catalog | 2 | 294 | 21 | 42 | 0,49 | 0 |
| catalog | 3 | 292 | 22 | 71 | 0,49 | 0 |
| **catalog** | **gộp** | 870 | 23 | **140** | 1,45 | 0 (0,00 %) |
| receipt | 1 | 283 | 38 | 366 | 0,47 | 0 |
| receipt | 2 | 293 | 24 | 50 | 0,49 | 0 |
| receipt | 3 | 290 | 25 | 142 | 0,48 | 0 |
| **receipt** | **gộp** | 866 | 27 | **218** | 1,44 | 0 (0,00 %) |

### 4.3. 20 VU

| Thao tác | Lần | Mẫu | p50 (ms) | p95 (ms) | Thông lượng (req/s) | Lỗi kỹ thuật |
|---|---|---:|---:|---:|---:|---:|
| hold | 1 | 1037 | 35 | 604 | 1,72 | 6 (0,58 %) |
| hold | 2 | 1137 | 32 | 113 | 1,90 | 0 |
| hold | 3 | 1175 | 31 | 74 | 1,96 | 0 |
| **hold** | **gộp** | 3349 | 33 | **122** | 5,57 | 6 (0,18 %) |
| adjust_hold | 1 | 1032 | 36 | 418 | 1,72 | 3 (0,29 %) |
| adjust_hold | 2 | 1138 | 33 | 126 | 1,90 | 0 |
| adjust_hold | 3 | 1174 | 33 | 67 | 1,96 | 0 |
| **adjust_hold** | **gộp** | 3344 | 34 | **131** | 5,57 | 3 (0,09 %) |
| send | 1 | 1036 | 64 | 452 | 1,71 | 8 (0,77 %) |
| send | 2 | 1135 | 55 | 166 | 1,89 | 0 |
| send | 3 | 1171 | 55 | 106 | 1,95 | 0 |
| **send** | **gộp** | 3342 | 57 | **183** | 5,56 | 8 (0,24 %) |
| read_order | 1 | 516 | 33 | 69 | 0,86 | 1 (0,19 %) |
| read_order | 2 | 561 | 42 | 64 | 0,94 | 0 |
| read_order | 3 | 584 | 45 | 64 | 0,97 | 0 |
| **read_order** | **gộp** | 1661 | 42 | **65** | 2,77 | 1 (0,06 %) |
| read_menu | 1 | 517 | 97 | 583 | 0,86 | 1 (0,19 %) |
| read_menu | 2 | 560 | 74 | 179 | 0,93 | 0 |
| read_menu | 3 | 583 | 72 | 139 | 0,97 | 0 |
| **read_menu** | **gộp** | 1660 | 78 | **213** | 2,77 | 1 (0,06 %) |
| catalog | 1 | 515 | 24 | 154 | 0,86 | 1 (0,19 %) |
| catalog | 2 | 559 | 24 | 63 | 0,93 | 0 |
| catalog | 3 | 583 | 23 | 43 | 0,97 | 0 |
| **catalog** | **gộp** | 1657 | 24 | **56** | 2,76 | 1 (0,06 %) |
| receipt | 1 | 513 | 31 | 269 | 0,85 | 0 |
| receipt | 2 | 560 | 27 | 112 | 0,93 | 0 |
| receipt | 3 | 583 | 26 | 54 | 0,97 | 0 |
| **receipt** | **gộp** | 1656 | 27 | **97** | 2,76 | 0 (0,00 %) |

### 4.4. Tài nguyên trong lúc đo (trung bình/đỉnh theo mẫu ~30 s)

| Lần chạy | Tải máy 1 phút (TB/đỉnh) | CPU rảnh toàn máy % (TB/thấp nhất) | CPU container CSDL % (TB/đỉnh) | RAM CSDL đỉnh (MiB) | Kết nối CSDL đỉnh | Thời gian chờ khóa hàng cộng dồn trong lần chạy (ms) / số lần chờ | CPU API % (TB/đỉnh) | RSS API đỉnh (MB) |
|---|---|---|---|---:|---:|---|---|---:|
| 5 VU · 1 | 6,8 / 11,7 | 54 / 2 | 6 / 11 | 926 | 6 | 3.963 / 88 | 4 / 12 | 205 |
| 5 VU · 2 | 5,4 / 8,8 | 58 / 9 | 5 / 11 | 956 | 6 | 1.750 / 68 | 2 / 7 | 205 |
| 5 VU · 3 | 5,4 / 7,4 | 64 / 7 | 5 / 10 | 958 | 6 | 8.581 / 85 | 3 / 11 | 206 |
| 10 VU · 1 | 15,3 / 25,7 | 24 / 0 | 9 / 20 | 984 | 11 | 88.228 / 577 | 6 / 17 | 208 |
| 10 VU · 2 | 5,6 / 8,7 | 61 / 22 | 9 / 17 | 996 | 6 | 6.327 / 302 | 6 / 18 | 209 |
| 10 VU · 3 | 8,6 / 11,5 | 43 / 7 | 8 / 17 | 1.012 | 8 | 48.965 / 330 | 5 / 12 | 208 |
| 20 VU · 1 | 11,6 / 14,9 | 23 / 0 | 10 / 22 | 1.135 | 16 | 1.866.367 / 1.437 | 11 / 25 | 204 |
| 20 VU · 2 | 9,5 / 19,9 | 42 / 0 | 13 / 22 | 1.218 | 16 | 922.897 / 1.408 | 11 / 33 | 206 |
| 20 VU · 3 | 3,9 / 7,0 | 67 / 13 | 13 / 20 | 1.227 | 6 | 31.706 / 1.254 | 10 / 27 | 204 |

Nhận xét: CPU của tiến trình API và của container CSDL đều thấp (≤ 33 % của một lõi), RSS của API ổn định ~205 MB;
máy chủ không bị nghẽn CPU do chính hệ thống được đo mà do tải của các tiến trình khác. Điểm đáng chú ý nằm ở cột
thời gian chờ khóa: tăng từ vài giây (5 VU) lên hàng nghìn giây cộng dồn ở 20 VU lần 1 và 2, trùng với các đợt
đứng hình mô tả ở mục 6. Số kết nối đỉnh 16 ở 20 VU phù hợp với pool API đã đầy (15 kết nối) cộng kết nối của chính bộ lấy mẫu; bộ đếm
toàn instance nên không tách riêng được.

## 5. Kết quả phát tải báo cáo (NFR-03)

5 phiên Quản lý, mỗi vòng gọi `revenue` theo ngày, `revenue` theo tháng và `dishes` (xếp hạng món); neo `anchor=2026-04-26`.
Doanh thu ngày kỳ vọng theo manifest 11.770.000 và doanh thu tháng 318.251.000; `load_reports` đối chiếu từng
phản hồi với manifest và **không ghi nhận lần lệch nào** (0 lỗi `manifest_revenue_mismatch`). Cache: xem mục 3.

| Báo cáo | Lần | Mẫu | p50 (ms) | p95 (ms) | Thông lượng (req/s) | Lỗi kỹ thuật |
|---|---|---:|---:|---:|---:|---:|
| revenue_day | 1 | 500 | 11 | 23 | 0,83 | 0 |
| revenue_day | 2 | 500 | 11 | 24 | 0,83 | 0 |
| revenue_day | 3 | 500 | 10 | 24 | 0,83 | 0 |
| **revenue_day** | **gộp** | 1500 | 10 | **24** | 2,50 | 0 (0,00 %) |
| revenue_month | 1 | 500 | 18 | 33 | 0,83 | 0 |
| revenue_month | 2 | 500 | 18 | 34 | 0,83 | 0 |
| revenue_month | 3 | 498 | 17 | 32 | 0,83 | 0 |
| **revenue_month** | **gộp** | 1498 | 18 | **33** | 2,50 | 0 (0,00 %) |
| ranking | 1 | 500 | 29 | 41 | 0,83 | 0 |
| ranking | 2 | 500 | 29 | 42 | 0,83 | 0 |
| ranking | 3 | 499 | 28 | 40 | 0,83 | 0 |
| **ranking** | **gộp** | 1499 | 29 | **41** | 2,50 | 0 (0,00 %) |

Cả ba loại báo cáo có p95 dưới 50 ms, thấp hơn ngưỡng 10 s hơn hai bậc độ lớn. Lưu ý phạm vi: dữ liệu là 20.000 order
trong 12 tháng và các truy vấn tổng hợp trực tiếp trên bảng giao dịch; kết luận chỉ áp dụng cho quy mô này.

## 6. Phân tích lỗi kỹ thuật và đuôi độ trễ ở 20 VU

**Hiện tượng.** Ở 20 VU, lần 1 và lần 2 xuất hiện các đợt đứng hình: nhiều request (mọi thao tác, kể cả đọc không
khóa như `read_menu`) cùng chạm mốc 30 s rồi hệ thống tự hồi phục.

| Lần | Thời điểm (giờ +07) | Giai đoạn | Hậu quả |
| --- | --- | --- | --- |
| 20 VU · 1 | 14:58:47 và 14:59:19–14:59:24 | khởi động | 40 lỗi kỹ thuật (ReadTimeout 30 s), bị loại khỏi số liệu |
| 20 VU · 1 | 15:05:15 | **cửa sổ đo** | 20 lỗi kỹ thuật trong số liệu, nhiều request kéo dài 2–4 s trước và sau đợt đứng |
| 20 VU · 2 | 15:12:xx–15:13:xx | khởi động | 29 lỗi kỹ thuật, bị loại; cửa sổ đo còn 28 request > 1 s |
| 20 VU · 3 | — | — | không có lỗi |

Log API (`api-biz-vu20-r1.log`: 42 `INTERNAL_ERROR`, 34 lần `QueuePool limit of size 5 overflow 10 reached,
connection timed out, timeout 30.00`; `api-biz-vu20-r2.log`: 20 và 16) xác nhận mọi lỗi phía máy chủ là
**cạn pool kết nối** SQLAlchemy. Độ trễ 30,0 s của các request lỗi trùng với `pool_timeout` mặc định.

**Cơ chế khả dĩ nhất (suy ra từ mã nguồn, chưa có thực nghiệm cô lập để kiểm chứng):**

- `orders._claim_display_number` (`apps/api/src/app/modules/sales/orders.py`, dòng 105–128) trên MySQL mở **kết nối thứ hai**
  (`get_engine().begin()`) để cấp mã order, trong khi giao dịch gửi món vẫn đang giữ kết nối thứ nhất.
  Nhiều traceback trong log dừng đúng ở dòng 115 này (12 lần ở lần 1, 8 lần ở lần 2).
- Mọi giao dịch làm thay đổi kho (giữ món, gửi món, nhập kho) đều khóa `SELECT ... FOR UPDATE` lên **một hàng cấu hình
  duy nhất** (`lock_stock_operations`, `apps/api/src/app/modules/inventory/stock.py`, dòng 153–161; gọi từ
  `reservations.py:242` và `inventory/service.py`), nhằm đóng băng giao dịch kho khi kiểm kê (NFR-20). Các giao dịch này
  vì vậy được tuần tự hóa toàn hệ thống.
- Khi nhiều giao dịch xếp hàng chờ khóa chung đó, chúng giữ hết 15 kết nối của pool; giao dịch đang nắm khóa lại cần
  kết nối thứ hai để cấp mã order và phải chờ pool, trong khi những giao dịch giữ kết nối lại đang chờ chính khóa đó.
  Đây là dạng bế tắc "khóa ↔ pool"; nó chỉ được phá khi `pool_timeout` 30 s hết hạn. Cách giải thích này khớp với
  cột thời gian chờ khóa cộng dồn (1,87 triệu ms ở lần 1) và với việc cả `read_menu`/`read_order` cũng bị đứng
  (chúng chỉ cần một kết nối trong pool đã cạn).
- Điều kiện kích hoạt hiếm hơn với tải thấp: ở 5 và 10 VU không có lỗi pool nào (có thể do số request đồng thời
  không đủ để cạn 15 kết nối; chưa đo số request đồng thời thực tế).

**Mức độ ảnh hưởng đến NFR-01.** p95 tính trên request thành công vẫn dưới 1 s. Để không che giấu đuôi, bảng sau
(`sensitivity.txt`) cho p95 khi **tính cả** mẫu lỗi kỹ thuật và tỷ lệ request thành công chậm hơn 1 s (gộp 3 lần):

| Mức tải | Thao tác | p95 thành công (ms) | p95 gồm cả lỗi (ms) | p99 thành công (ms) | Tỷ lệ > 1 s | Độ trễ tối đa (ms) |
|---|---|---:|---:|---:|---:|---:|
| 10 VU | hold | 200 | 200 | 880 | 0,92 % | 3.327 |
| 10 VU | send | 272 | 272 | 880 | 0,86 % | 3.988 |
| 20 VU | hold | 122 | 127 | 1.611 | 1,38 % | 21.451 |
| 20 VU | send | 183 | 190 | 1.478 | 1,29 % | 4.171 |
| 20 VU | read_menu | 213 | 214 | 1.112 | 1,33 % | 20.598 |

Nghĩa là NFR-01 (đặt trên p95) vẫn đạt kể cả khi tính các mẫu lỗi, nhưng khoảng 1–1,4 % request ở 10–20 VU chậm hơn
1 s và các đợt đứng 30 s là lỗi độ tin cậy thực sự, sẽ bộc lộ rõ hơn nếu tăng tải hoặc rút ngắn thời gian nghỉ giữa
thao tác.

**Lưu ý về nhiễu.** p95 gộp ở 10 VU (tối đa 272 ms) cao hơn ở 20 VU (tối đa 183 ms); điều này không phản ánh hệ
thống nhanh hơn khi tải tăng mà là nhiễu từ máy dùng chung: lần 1 của mỗi mức hầu hết các thao tác có p95 cao hơn lần 2–3 (ví dụ
10 VU lần 1: `send` 548 ms so với 103 và 145 ms), và lần 1 ở 10 VU trùng với tải máy đỉnh 25,7. Các lần lặp khác nhau
một bậc độ lớn là lý do báo cáo phải dùng p95 gộp và công bố từng lần lặp thay vì một con số trung bình.

**Đề xuất (chưa thực hiện, không nằm trong phạm vi đo):** (1) cấp mã order không dùng kết nối thứ hai khi đã giữ
kết nối (ví dụ dùng cùng giao dịch với khóa theo ngày, hoặc đặt trước khi giữ khóa kho); (2) tăng `pool_size`/`max_overflow`
hoặc đặt `pool_timeout` ngắn hơn để lỗi nổi lên nhanh; (3) cân nhắc giảm phạm vi khóa toàn cục `lock_stock_operations`
(khóa dạng chia sẻ cho giao dịch thường, khóa độc quyền chỉ khi mở kiểm kê); (4) lặp lại 20 VU trên máy cô lập để
tách ảnh hưởng của tải nền, và thử 30–40 VU để xác định điểm bão hòa.

**Cập nhật sau đợt đo.** Đề xuất (1) đã thực hiện ở commit `09a9cc5`: mã order được cấp qua một pool kết nối riêng
(2 + 3 kết nối) nên giao dịch đang giữ kết nối chính không còn tranh pool với chính các giao dịch đang chờ nó. Kiểm thử
`test_mysql_order_counter.py` dựng đúng tình huống pool chính đã cạn (1 kết nối, đang bị giữ) và vẫn cấp được mã. Mọi
số liệu trong tài liệu này đo trên `a5dbec1`, **trước** khi sửa; chưa đo lại 20 VU sau khi sửa.

## 7. Kiểm tra sau chạy (J.7)

`verify_perf.py` kiểm tra: tồn kho = tổng sổ cái theo từng lô và từng nguyên liệu, không tồn âm, không đặt giữ vượt
lô, khả dụng khớp với các lượt giữ còn hiệu lực, không tiêu hao lặp một dòng/lô, không `request_id` gửi trùng, không
lượt giữ gắn hai dòng order; và so tổng doanh thu lịch sử với manifest.

| Mốc | Kết quả | Orders | Giao dịch kho | Lô | Tổng doanh thu |
| --- | --- | ---:| ---:| ---:| --- |
| Ngay sau seed (bản sao gốc) | 0 lỗi | 20.000 | 63.135 | 30 | 3.739.234.000 |
| Sau 5 VU lần 1/2/3 | 0 lỗi | 20.362 / 20.364 / 20.364 | 63.678 / 63.681 / 63.681 | 211 / 212 / 212 | không đổi |
| Sau 10 VU lần 1/2/3 | 0 lỗi | 20.702 / 20.722 / 20.710 | 64.188 / 64.218 / 64.200 | 381 / 391 / 385 | không đổi |
| Sau 20 VU lần 1/2/3 | 0 lỗi | 21.145 / 21.296 / 21.428 | 64.847 / 65.071 / 65.277 | 597 / 670 / 744 | không đổi |
| Sau báo cáo lần 1/2/3 | 0 lỗi | 20.000 (cả ba) | 63.135 | 30 | không đổi |

Kể cả ở các lần 20 VU có đợt đứng 30 s và 60 lỗi kỹ thuật, không phát sinh tồn âm, tiêu hao lặp hay gửi trùng: `verify_perf`
không phát hiện trạng thái dở dang nào từ các giao dịch bị hủy do hết thời gian chờ. Lưu ý phạm vi của kiểm tra: `verify_perf`
chỉ so *tổng doanh thu lịch sử* với baseline (số bản ghi tăng sau tải là đúng kỳ vọng), và các kịch bản tranh chấp
cùng nguyên liệu/giữ hết hạn theo mục 5.2.4 không thuộc lần chạy này.

## 8. Kết luận

- **NFR-01: đạt theo tiêu chí p95 ở cả 3 mức tải** (p95 gộp lớn nhất 272 ms; mọi lần lặp đơn lẻ dưới 0,61 s).
  Điều kiện đi kèm: ở 20 VU có lỗi độ tin cậy (cạn pool kết nối, đợt đứng 30 s, 20 lỗi kỹ thuật trong cửa sổ đo của lần 1).
  Theo J.6 các lỗi này phải được ghi nhận và điều tra; nguyên nhân khả dĩ nêu ở mục 6 nhưng chưa được kiểm chứng
  bằng thực nghiệm riêng, và không nên dùng kết quả này để khẳng định hệ thống chịu được 20 VU "không lỗi".
- **NFR-03: đạt** (p95 gộp 24 / 33 / 41 ms, thấp hơn 10 s rất nhiều), doanh thu khớp manifest ở mọi phản hồi.
- Bất biến dữ liệu sau tải được giữ ở cả 13 lượt kiểm tra.
- Giới hạn của kết quả: máy dùng chung và nhiễu cao (mục 2), một tiến trình API, tải sinh trên cùng máy, thời gian
  nghỉ 1–3 s làm thông lượng thấp (tối đa ~5,6 req/s cho mỗi thao tác chính), bộ đệm InnoDB 128 MiB mặc định.

## 9. Bằng chứng và cách chạy lại

Thư mục `docs/testing/artifacts/2026-10-27-perf/` (tổng ~9 MB, không cần nén):

- `biz-vu{05,10,20}-r{1,2,3}.csv|.json`, `rep-vu05-r{1,2,3}.csv|.json`: CSV từng request (có cả giai đoạn khởi động, cột `phase`) và tóm tắt của công cụ.
- `resources-*.csv`: mẫu tài nguyên theo thời gian cho từng lần chạy.
- `verify-*.slim.json`: kết quả `verify_perf` (bản đầy đủ ~12 MB mỗi lượt không lưu, vì chứa sổ cái 63–65 nghìn dòng đã có trong `manifest.json.gz`).
- `manifest.json.gz`: manifest của seed (số bản ghi, tồn theo lô, sổ cái, tổng tiền theo ngày, checksum).
- `api-*.log`: log máy chủ API từng lần chạy (chứa các traceback ở mục 6); `driver.log`, `seed.log`: nhật ký điều khiển và seed.
- `driver.sh` (tập lệnh chạy tuần tự), `analyze.py`, `sensitivity.py`, `analysis.txt`, `sensitivity.txt`: tập lệnh và đầu ra dùng để tạo các bảng trên.
- Không lưu `accounts.json` (chứa mật khẩu tài khoản thử) và không lưu thông tin kết nối CSDL.

`driver.sh` đọc URL CSDL từ một tệp cục bộ không được lưu kèm; để chạy lại cần tạo CSDL `perf_` mới, migrate, seed theo
mục 3, rồi đặt các biến `PERF_URL` và đường dẫn tương ứng. Cần nhắc: các tệp trong thư mục `artifacts` chưa được
commit theo yêu cầu của lần chạy này.
