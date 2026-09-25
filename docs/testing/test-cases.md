# Test case theo module

Quy ước mã: `TC-<MODULE>-nn` (2 chữ số, không nhảy số qua các lần chỉnh sửa tài liệu). Cột **Loại** ghi
`Tự động: <file>::<hàm test>` khi có test tương ứng trong `apps/api/tests` (pytest) hoặc
`apps/web/src/**/*.test.tsx` (vitest); nếu chưa có, ghi `Thủ công`. Cột **Kết quả** để trống cho người
thực hiện tick khi chạy kiểm thử thủ công: ☐ Đạt ☐ Không đạt.

Business Date (06:00 → 06:00 hôm sau) được viết tắt **BD**. Ví dụ mã order: `ORD-250926-042`
(order thứ 042 của BD 26/09/2025).

---

## 1. Module Danh mục (FR-CAT-01 → FR-CAT-28)

| Mã TC | FR | Vai trò | Tiền điều kiện | Các bước | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-CAT-01 | FR-CAT-01 | Quản lý | Có ≥ 3 nhóm món | Sắp xếp lại thứ tự 3 nhóm, bỏ sót 1 nhóm trong payload | Yêu cầu bị từ chối, thứ tự cũ giữ nguyên | Tự động: `test_catalog_dishes.py::test_a_reorder_that_omits_a_group_is_refused` | ☐ Đạt ☐ Không đạt |
| TC-CAT-02 | FR-CAT-01 | Quản lý | 3 nhóm món đã có `display_order` | Gửi thứ tự mới đầy đủ | `display_order` được đánh số lại đúng thứ tự gửi lên | Tự động: `test_catalog_dishes.py::test_reordering_groups_renumbers_them` | ☐ Đạt ☐ Không đạt |
| TC-CAT-03 | FR-CAT-01 | Quản lý | Đã có 3 nhóm | Tạo nhóm món mới | Nhóm mới có `display_order` lớn nhất (cuối danh sách) | Tự động: `test_catalog_dishes.py::test_a_new_group_goes_to_the_end_of_the_list` | ☐ Đạt ☐ Không đạt |
| TC-CAT-04 | FR-CAT-02 | Quản lý | Có 1 nhóm món | Tạo món ăn với tên, giá bán, nhóm, hình ảnh | Món tạo thành công, giữ đủ 4 thuộc tính | Tự động: `test_catalog_dishes.py::test_a_dish_carries_a_name_a_price_a_group_and_a_picture` | ☐ Đạt ☐ Không đạt |
| TC-CAT-05 | FR-CAT-02 | Quản lý | Có 3 món cùng/khác tên | Tìm kiếm theo tên (khớp một phần) | Trả về đúng món khớp tên | Tự động: `test_catalog_dishes.py::test_dishes_can_be_searched_by_name` | ☐ Đạt ☐ Không đạt |
| TC-CAT-06 | FR-CAT-02 | Quản lý | Có 2 nhóm món | Gán món vào 2 nhóm cùng lúc (payload sai) | Bị từ chối, món chỉ thuộc đúng một nhóm | Tự động: `test_catalog_dishes.py::test_a_dish_belongs_to_exactly_one_group` | ☐ Đạt ☐ Không đạt |
| TC-CAT-07 | FR-CAT-03 | Quản lý | Nhóm còn ≥ 1 món chưa xóa mềm | Xóa nhóm món | Bị từ chối | Tự động: `test_catalog_dishes.py::test_a_group_with_live_dishes_cannot_be_deleted` | ☐ Đạt ☐ Không đạt |
| TC-CAT-08 | FR-CAT-03 | Quản lý | Toàn bộ món trong nhóm đã xóa mềm | Xóa nhóm món | Xóa thành công | Tự động: `test_catalog_dishes.py::test_a_group_can_be_deleted_once_every_dish_is_soft_deleted` | ☐ Đạt ☐ Không đạt |
| TC-CAT-09 | FR-CAT-04 | Quản lý | Món đã có trong order lịch sử | Xóa món | Món chuyển `DaXoa=1`, vẫn còn trong DB, không có API xóa vĩnh viễn | Tự động: `test_catalog_dishes.py::test_a_dish_is_never_hard_deleted` | ☐ Đạt ☐ Không đạt |
| TC-CAT-10 | FR-CAT-04, FR-SET-08 | Quản lý | Món tồn tại | Xóa mềm món | Audit log ghi nhận thao tác xóa | Tự động: `test_catalog_dishes.py::test_dish_deletion_is_audited` | ☐ Đạt ☐ Không đạt |
| TC-CAT-11 | FR-CAT-05 | Quản lý | Món có thay đổi giá 'chờ áp dụng' | Xóa mềm món | Thay đổi giá đang chờ tự động bị hủy | Tự động: `test_catalog_dishes.py::test_soft_deleting_a_dish_cancels_its_pending_changes` | ☐ Đạt ☐ Không đạt |
| TC-CAT-12 | FR-CAT-06 | Quản lý | — | Tạo món mới, chưa gán công thức | Món ở trạng thái 'Nháp', không xuất hiện màn hình gọi món | Tự động: `test_catalog_dishes.py::test_a_new_dish_starts_as_draft` | ☐ Đạt ☐ Không đạt |
| TC-CAT-13 | FR-CAT-07 | Quản lý | Món ở trạng thái 'Nháp' | Gán công thức: danh sách nguyên liệu + định lượng | Công thức lưu đúng nguyên liệu/định lượng theo đơn vị nguyên liệu | Tự động: `test_catalog_recipes.py::test_a_recipe_line_carries_no_unit_of_its_own` | ☐ Đạt ☐ Không đạt |
| TC-CAT-14 | FR-CAT-07 | Quản lý | Món đã có công thức | Nhập định lượng 0 hoặc âm cho một nguyên liệu | Bị từ chối | Tự động: `test_catalog_recipes.py::test_a_zero_or_negative_quantity_is_rejected` | ☐ Đạt ☐ Không đạt |
| TC-CAT-15 | FR-CAT-08 | Quản lý | Món đã có công thức áp dụng | Lên lịch công thức mới cho BD kế tiếp | Công thức mới có hiệu lực đúng 06:00 BD đã chọn; order tạo trước đó vẫn dùng công thức cũ | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-CAT-16 | FR-CAT-08 | Quản lý | — | Chọn BD đã bắt đầu/đã kết thúc để lên lịch công thức | Bị từ chối | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-CAT-17 | FR-CAT-09 | Quản lý | Món có công thức | Tạo 2 thay đổi công thức 'chờ áp dụng' liên tiếp | Chỉ giữ thay đổi mới nhất | Tự động: `test_catalog_recipes.py::test_only_one_pending_recipe_change_per_dish` | ☐ Đạt ☐ Không đạt |
| TC-CAT-18 | FR-CAT-10, FR-SET-08 | Quản lý | Có thay đổi công thức 'chờ áp dụng' | Hủy thay đổi trước khi có hiệu lực | Hủy thành công, ghi audit log | Tự động: `test_catalog_recipes.py::test_cancelling_a_pending_recipe_change_is_audited` | ☐ Đạt ☐ Không đạt |
| TC-CAT-19 | FR-CAT-11 | Quản lý | Món 'Nháp', kho đủ nguyên liệu | Gán công thức lần đầu | Món chuyển 'Hoạt động' (hoặc 'Hết nguyên liệu' nếu kho không đủ) | Tự động: `test_catalog_recipes.py::test_the_first_recipe_activates_the_dish` | ☐ Đạt ☐ Không đạt |
| TC-CAT-20 | FR-CAT-12 | Quản lý, Nhân viên kho | — | Thêm/sửa/xóa/tìm kiếm nguyên liệu | Thao tác thành công, tìm kiếm trả đúng kết quả | Tự động: `test_catalog_ingredients.py::test_ingredients_can_be_searched_by_name` | ☐ Đạt ☐ Không đạt |
| TC-CAT-21 | FR-CAT-12 | Quản lý | Nguyên liệu không cấu hình mức tồn riêng | Đọc mức tồn tối thiểu áp dụng | Dùng đúng mức mặc định hệ thống | Tự động: `test_catalog_ingredients.py::test_an_ingredient_without_its_own_threshold_uses_the_default` | ☐ Đạt ☐ Không đạt |
| TC-CAT-22 | FR-CAT-12 (phân quyền) | Nhân viên kho | — | Nhân viên kho thử quản lý nguyên liệu, sau đó thử quản lý món ăn | Quản lý nguyên liệu: thành công. Quản lý món ăn: 403 | Tự động: `test_catalog_ingredients.py::test_warehouse_staff_may_manage_ingredients_but_not_dishes` | ☐ Đạt ☐ Không đạt |
| TC-CAT-23 | FR-CAT-13, FR-SET-08 | Nhân viên kho | Nguyên liệu đã dùng trong công thức | Xóa nguyên liệu | Chỉ xóa mềm, ghi audit log | Tự động: `test_catalog_ingredients.py::test_deleting_a_referenced_ingredient_is_soft_only`, `test_ingredient_deletion_is_audited` | ☐ Đạt ☐ Không đạt |
| TC-CAT-24 | FR-CAT-14 | Nhân viên kho | Nguyên liệu chưa từng tham chiếu | Sửa đơn vị tính | Sửa thành công | Tự động: `test_catalog_ingredients.py::test_the_unit_can_still_be_changed_before_any_reference` | ☐ Đạt ☐ Không đạt |
| TC-CAT-25 | FR-CAT-14 | Nhân viên kho | Nguyên liệu đã có phiếu nhập/dùng trong công thức | Sửa đơn vị tính | Bị khóa, không cho sửa | Tự động: `test_catalog_ingredients.py::test_the_unit_is_locked_once_the_ingredient_is_referenced` | ☐ Đạt ☐ Không đạt |
| TC-CAT-26 | FR-CAT-15 | Quản lý, Nhân viên kho | Nhà cung cấp đã có lịch sử nhập | Xem chi tiết nhà cung cấp | Hiển thị đúng lịch sử nhập hàng | Tự động: `test_catalog_ingredients.py::test_a_supplier_shows_its_receipt_history` | ☐ Đạt ☐ Không đạt |
| TC-CAT-27 | FR-CAT-16 | Quản lý | Nhà cung cấp chưa từng nhập hàng | Xóa nhà cung cấp | Xóa vĩnh viễn | Tự động: `test_catalog_ingredients.py::test_a_supplier_with_no_history_is_deleted_outright` | ☐ Đạt ☐ Không đạt |
| TC-CAT-28 | FR-CAT-16 | Quản lý | Nhà cung cấp đã có lịch sử nhập | Xóa nhà cung cấp | Chỉ xóa mềm | Tự động: `test_catalog_ingredients.py::test_a_supplier_with_receipts_is_only_soft_deleted` | ☐ Đạt ☐ Không đạt |
| TC-CAT-29 | FR-CAT-17 (phân quyền) | Thu ngân/NV order | — | Mở sơ đồ bàn, thử sửa/xóa một bàn | Xem được trạng thái bàn; sửa/xóa bị 403 | Tự động: `test_catalog_tables.py::test_the_cashier_sees_the_floor_plan_but_cannot_edit_it` | ☐ Đạt ☐ Không đạt |
| TC-CAT-30 | FR-CAT-18 | Thu ngân/NV order | Bàn 'Trống' | Tạo order cho bàn, sau đó thanh toán thành công | Bàn chuyển 'Đang phục vụ' khi tạo order, về 'Trống' khi thanh toán xong | Tự động: `test_sales_orders.py::test_submit_takes_price_and_recipe`, `test_sales_locking_and_search.py::test_settled_rejects_mutation` | ☐ Đạt ☐ Không đạt |
| TC-CAT-31 | FR-CAT-19 | Quản lý | Bàn ở trạng thái 'Đang phục vụ' | Xóa bàn | Bị từ chối | Tự động: `test_catalog_tables.py::test_a_table_in_use_cannot_be_deleted` | ☐ Đạt ☐ Không đạt |
| TC-CAT-32 | FR-CAT-19 | Quản lý | Bàn đã từng gắn order lịch sử | Xóa bàn | Chỉ xóa mềm, ẩn khỏi sơ đồ bàn nhưng tên được giải phóng | Tự động: `test_catalog_tables.py::test_a_soft_deleted_table_frees_its_name`, `test_soft_deleted_table_is_hidden_from_the_floor_plan` | ☐ Đạt ☐ Không đạt |
| TC-CAT-33 | FR-CAT-20 | Quản lý | Món đang bán | Cập nhật giá, chọn BD kế tiếp làm mặc định | BD mặc định = BD kế tiếp; giá cũ vẫn áp dụng cho order trước hiệu lực | Tự động: `test_catalog_prices.py::test_the_default_target_is_the_next_business_date`, `test_the_active_version_is_the_one_in_force_on_that_business_date` | ☐ Đạt ☐ Không đạt |
| TC-CAT-34 | FR-CAT-20 | Quản lý | — | Lên lịch giá cho BD đã bắt đầu/đã kết thúc | Bị từ chối | Tự động: `test_catalog_prices.py::test_a_scheduled_change_must_target_a_future_business_date` | ☐ Đạt ☐ Không đạt |
| TC-CAT-35 | FR-CAT-21 | Quản lý | Món có 1 thay đổi giá 'chờ áp dụng' | Tạo thay đổi giá 'chờ áp dụng' thứ hai | Thay đổi mới ghi đè thay đổi cũ | Tự động: `test_catalog_prices.py::test_only_one_change_waits_per_dish_and_the_newest_wins` | ☐ Đạt ☐ Không đạt |
| TC-CAT-36 | FR-CAT-22, FR-SET-08 | Quản lý | Có thay đổi giá 'chờ áp dụng' | Hủy thay đổi giá đang chờ | Hủy thành công, ghi audit log | Tự động: `test_catalog_prices.py::test_cancelling_a_pending_change_is_audited` | ☐ Đạt ☐ Không đạt |
| TC-CAT-37 | FR-CAT-23, FR-CAT-25, FR-SET-08 | Quản lý | Món đang có giá áp dụng | Sửa trực tiếp giá bán | Áp dụng ngay, ghi thành phiên bản mới, ghi audit log | Tự động: `test_catalog_prices.py::test_a_direct_edit_applies_now_and_keeps_the_scheduled_change` | ☐ Đạt ☐ Không đạt |
| TC-CAT-38 | FR-CAT-24 | Quản lý | Món vừa có sửa trực tiếp vừa có lịch BD đang chờ | Kiểm tra thay đổi theo lịch sau khi sửa trực tiếp | Thay đổi theo lịch không bị hủy/ghi đè | Tự động: `test_catalog_prices.py::test_a_direct_edit_applies_now_and_keeps_the_scheduled_change` | ☐ Đạt ☐ Không đạt |
| TC-CAT-39 | FR-CAT-26 | Quản lý | Món 'Hoạt động' | Ẩn thủ công một món | Món biến mất khỏi màn hình gọi món, độc lập với trạng thái tồn kho | Tự động: `test_catalog_tables.py::test_manual_hiding_is_independent_of_stock` | ☐ Đạt ☐ Không đạt |
| TC-CAT-40 | FR-CAT-27 | Hệ thống | Món hết nguyên liệu VÀ bị ẩn thủ công cùng lúc | Bổ sung đủ nguyên liệu nhưng chưa bật hiện lại thủ công | Món vẫn ẩn (cần cả hai nguyên nhân đều tắt mới hiện) | Tự động: `test_catalog_tables.py::test_the_two_out_of_stock_causes_are_independent` | ☐ Đạt ☐ Không đạt |
| TC-CAT-41 | FR-CAT-28 | Quản lý | Món đã xóa mềm | Kiểm tra trạng thái vận hành của món đã xóa | Trạng thái xóa mềm độc lập, không lẫn với Hoạt động/Hết nguyên liệu/Nháp | Tự động: `test_catalog_tables.py::test_soft_delete_is_a_state_of_its_own` | ☐ Đạt ☐ Không đạt |

## 2. Module Bán hàng (FR-SALE-01 → FR-SALE-29)

| Mã TC | FR | Vai trò | Tiền điều kiện | Các bước | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SALE-01 | FR-SALE-01, FR-SALE-03 | Thu ngân/NV order | Bàn 'Trống', món 'Hoạt động', đủ tồn | Chọn bàn, chọn món, Submit | Order tạo thành công với giá và công thức tại thời điểm submit | Tự động: `test_sales_orders.py::test_submit_takes_price_and_recipe` | ☐ Đạt ☐ Không đạt |
| TC-SALE-02 | FR-SALE-01 | Thu ngân/NV order | — | Đánh dấu đơn 'Mang về', không chọn bàn | Order tạo thành công, `MaBan = null` | Tự động: `test_sales_orders.py::test_takeaway_no_table` | ☐ Đạt ☐ Không đạt |
| TC-SALE-03 | FR-SALE-02 | Thu ngân/NV order | Order đang mở | Thêm ghi chú "không hành" cho một dòng món | Ghi chú lưu đúng dòng món, không đổi công thức/trừ kho | Tự động: `test_sales_tickets.py::test_ticket_carries_info` | ☐ Đạt ☐ Không đạt |
| TC-SALE-04 | FR-SALE-03 | Thu ngân/NV order | — | Chọn món nhưng không bấm Submit | Không có order nào được ghi nhận | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-05 | FR-SALE-04 | Thu ngân/NV order | BD hiện tại chưa có order nào | Tạo 2 order liên tiếp trong cùng BD | Mã order dạng `ORD-ddMMyy-001`, `ORD-ddMMyy-002` tăng tuần tự | Tự động: `test_sales_orders.py::test_display_code_counts` | ☐ Đạt ☐ Không đạt |
| TC-SALE-06 | FR-SALE-05 | Thu ngân/NV order | Order gồm 1 món đủ tồn + 1 món vừa hết tồn | Submit order | Món đủ tồn được tạo, món hết tồn bị từ chối kèm lý do, order vẫn tạo với món hợp lệ | Tự động: `test_sales_orders.py::test_rejected_when_out_of_stock` | ☐ Đạt ☐ Không đạt |
| TC-SALE-07 | FR-SALE-05 | Thu ngân/NV order | Toàn bộ món trong order đều hết tồn | Submit order | Trả về lỗi 422, không tạo order | Tự động: `test_sales_orders.py::test_all_fail_returns_422` | ☐ Đạt ☐ Không đạt |
| TC-SALE-08 | FR-SALE-06, FR-SALE-27 | Thu ngân/NV order | Order đang mở | Thêm món mới vào order | Món thêm thành công, in bổ sung phiếu bếp | Tự động: `test_sales_tickets.py::test_adding_dish_prints_additional_ticket` | ☐ Đạt ☐ Không đạt |
| TC-SALE-09 | FR-SALE-07 | Thu ngân/NV order | Dòng món ở 'Đã xác nhận xong' | Thử sửa số lượng/xóa dòng món | Bị từ chối | Tự động: `test_sales_line_lifecycle.py::test_confirmed_line_cannot_cancel` | ☐ Đạt ☐ Không đạt |
| TC-SALE-10 | FR-SALE-08 | Thu ngân/NV order | Món đã có trong order, tồn không đủ cho phần tăng thêm | Tăng số lượng dòng món | Bị từ chối | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-09b | FR-SALE-09 | Thu ngân/NV order | Order chưa thanh toán | Gọi thêm món trong cùng order | Thêm thành công, không tạo order mới | Tự động: `test_sales_tickets.py::test_adding_dish_prints_additional_ticket` | ☐ Đạt ☐ Không đạt |
| TC-SALE-11 | FR-SALE-10 | Thu ngân/NV order | Dòng món 'Chờ làm' | Cập nhật lần lượt sang 'Đã xác nhận xong' rồi 'Đã phục vụ' | Trạng thái chỉ tiến, không lùi/nhảy cóc trái quy tắc | Tự động: `test_sales_line_lifecycle.py::test_status_only_moves_forward` | ☐ Đạt ☐ Không đạt |
| TC-SALE-12 | FR-SALE-11 | Thu ngân/NV order | Dòng món 'Chờ làm' | Hủy dòng món | Hủy thành công, hoàn kho, ghi audit (người, thời điểm, số lượng, lý do) | Tự động: `test_sales_line_lifecycle.py::test_waiting_line_cancel_returns_stock` | ☐ Đạt ☐ Không đạt |
| TC-SALE-13 | FR-SALE-12 | Thu ngân/NV order | Order chỉ có 1 dòng món, đang 'Chờ làm' | Hủy dòng món cuối cùng | Order tự đóng: không hóa đơn, bàn về Trống, hoàn kho đầy đủ | Tự động: `test_sales_line_lifecycle.py::test_cancelling_the_last_live_line_auto_closes_order` | ☐ Đạt ☐ Không đạt |
| TC-SALE-14 | FR-SALE-13, FR-SET-08 | Thu ngân/NV order | Order đang mở, có bàn 'Trống' khác | Đổi bàn cho order | Bàn đích 'Đang phục vụ', bàn nguồn 'Trống', ghi audit log | Tự động: `test_sales_line_lifecycle.py::test_move_table` | ☐ Đạt ☐ Không đạt |
| TC-SALE-15 | FR-SALE-13 | Thu ngân/NV order | Bàn đích đang 'Đang phục vụ' | Đổi bàn sang bàn đích đó | Bị từ chối | Tự động: `test_sales_line_lifecycle.py::test_move_to_occupied_refused` | ☐ Đạt ☐ Không đạt |
| TC-SALE-16 | FR-SALE-14 | Thu ngân | Order chưa thanh toán | Chọn phương thức tiền mặt | Thanh toán ghi nhận thành công | Tự động: `test_sales_payments.py::test_cash_payment` | ☐ Đạt ☐ Không đạt |
| TC-SALE-17 | FR-SALE-15 | Thu ngân | Order chưa thanh toán | Chọn thanh toán QR | Giao dịch QR tạo đúng số tiền phải thu, trạng thái 'Chờ xác nhận' | Tự động: `test_sales_payments.py::test_qr_starts` | ☐ Đạt ☐ Không đạt |
| TC-SALE-18 | FR-SALE-15 | Thu ngân | Giao dịch QR đang 'Chờ xác nhận' còn hiệu lực | Tạo thêm giao dịch QR thứ hai cho cùng order | Bị từ chối | Tự động: `test_sales_payments.py::test_second_qr_refused` | ☐ Đạt ☐ Không đạt |
| TC-SALE-19 | FR-SALE-16 | Hệ thống (webhook) | Giao dịch QR 'Chờ xác nhận' | Gửi webhook hợp lệ đúng số tiền | Giao dịch chuyển 'Thành công' | Tự động: `test_sales_payments.py::test_webhook_settles` | ☐ Đạt ☐ Không đạt |
| TC-SALE-20 | FR-SALE-16 | Hệ thống (webhook) | Giao dịch đã 'Thành công' | Gửi lại đúng webhook đó (trùng) | Idempotent: không tạo hóa đơn/ghi doanh thu lần 2 | Tự động: `test_sales_payments.py::test_webhook_idempotent` | ☐ Đạt ☐ Không đạt |
| TC-SALE-21 | FR-SALE-16 | Hệ thống (webhook) | Giao dịch QR đang chờ | Gửi webhook sai chữ ký/không xác định được giao dịch | Bị từ chối, ghi log | Tự động: `test_sales_payments.py::test_webhook_bad_sig` | ☐ Đạt ☐ Không đạt |
| TC-SALE-22 | FR-SALE-17 | Thu ngân | Giao dịch QR quá 10 phút chưa xác nhận | Kiểm tra trạng thái giao dịch | Chuyển 'Hết hạn' | Tự động: `test_sales_payments.py::test_qr_expires_after_ten_minutes_on_get_order` | ☐ Đạt ☐ Không đạt |
| TC-SALE-23 | FR-SALE-17 | Thu ngân | Giao dịch QR 'Hết hạn' | Chuyển sang 'Chờ đối soát' | Chuyển trạng thái thành công; không cho tạo QR mới trong lúc đó | Tự động: `test_sales_reconciliation.py::test_expire_to_reconcile`, `test_new_qr_refused_when_reconcile_pending` | ☐ Đạt ☐ Không đạt |
| TC-SALE-24 | FR-SALE-18 | Thu ngân | Order 'Chờ đối soát' | Nhập mã giao dịch ngân hàng, đính kèm ảnh chứng từ | Thông tin lưu lại, order vẫn 'Chờ đối soát' chờ Quản lý xác nhận | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-25 | FR-SALE-18 | Thu ngân | Order 'Chờ đối soát' | Thu ngân tự xác nhận kết quả đối soát | Bị từ chối — chỉ Quản lý được xác nhận | Tự động: `test_sales_reconciliation.py::test_only_manager_resolve` | ☐ Đạt ☐ Không đạt |
| TC-SALE-26 | FR-SALE-18 | Quản lý | Order 'Chờ đối soát', đã có mã giao dịch | Chọn 'Xác nhận đã nhận tiền' | Giao dịch 'Thành công', hóa đơn tự phát hành, ghi audit log đầy đủ | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-27 | FR-SALE-18 | Quản lý | Order 'Chờ đối soát' | Chọn 'Không có giao dịch' | Giao dịch chuyển 'Tranh chấp' | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-28 | FR-SALE-19 | Thu ngân | Thanh toán thành công | In hóa đơn | Hóa đơn đủ chi tiết món, thành tiền, tổng tiền, không tách VAT | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SALE-29 | FR-SALE-20 | Thu ngân | Order đã tất toán | Thử sửa/hủy món, hủy hóa đơn, thanh toán lại | Toàn bộ bị khóa/từ chối | Tự động: `test_sales_locking_and_search.py::test_settled_rejects_mutation` | ☐ Đạt ☐ Không đạt |
| TC-SALE-30 | FR-SALE-21 | Hệ thống | Có giao dịch bán hàng | Kiểm tra bản ghi giao dịch | Có mốc thời gian chi tiết phục vụ báo cáo/AI | Thủ công (đối chiếu dữ liệu seed) | ☐ Đạt ☐ Không đạt |
| TC-SALE-31 | FR-SALE-22 | Thu ngân | Có nhiều order trong nhiều BD | Tra cứu theo mã order, theo bàn, theo khoảng BD | Trả đúng kết quả cho từng tiêu chí | Tự động: `test_sales_locking_and_search.py::test_search_orders` | ☐ Đạt ☐ Không đạt |
| TC-SALE-32 | FR-SALE-23 | Thu ngân | Hóa đơn đã chốt | In lại hóa đơn | Nội dung giống hệt bản gốc, không cho sửa | Tự động: `test_sales_locking_and_search.py::test_reprint_invoice` | ☐ Đạt ☐ Không đạt |
| TC-SALE-33 | FR-SALE-24 | Thu ngân | Order chưa thanh toán | Thu ngân thử hủy toàn bộ order | Bị từ chối (chỉ Quản lý) | Tự động: `test_sales_line_lifecycle.py::test_only_manager_cancel_whole` | ☐ Đạt ☐ Không đạt |
| TC-SALE-34 | FR-SALE-24 | Quản lý | Order chưa thanh toán, có món 'Đã xác nhận xong' | Hủy toàn bộ order, không nhập lý do | Bị từ chối (bắt buộc lý do) | Tự động: `test_sales_line_lifecycle.py::test_cancel_whole_requires_reason` | ☐ Đạt ☐ Không đạt |
| TC-SALE-35 | FR-SALE-25 | Quản lý | Order đang 'Chờ xác nhận thanh toán' (QR còn hiệu lực) | Hủy toàn bộ order | Bị từ chối cho tới khi QR bị hủy/hết hạn | Tự động: `test_sales_line_lifecycle.py::test_cancel_order_refused_while_qr_pending` | ☐ Đạt ☐ Không đạt |
| TC-SALE-36 | FR-SALE-25 | Quản lý | QR vừa hết hạn/vừa bị hủy | Hủy toàn bộ order | Cho phép hủy | Tự động: `test_sales_line_lifecycle.py::test_cancel_order_allowed_after_qr_expired`, `test_cancel_order_allowed_after_qr_cancelled` | ☐ Đạt ☐ Không đạt |
| TC-SALE-37 | FR-SALE-26 | Quản lý | Order có dòng 'Chờ làm' và dòng 'Đã xác nhận xong' | Hủy toàn bộ order | Không hóa đơn, bàn về Trống, chỉ hoàn kho dòng 'Chờ làm', ghi vào báo cáo order bị hủy | Tự động: `test_reports_comparison.py::test_the_cancelled_report_lists_totals_counts_and_reasons` | ☐ Đạt ☐ Không đạt |
| TC-SALE-38 | FR-SALE-27 | Hệ thống | Order vừa submit hoặc thêm món | Kiểm tra lệnh in phiếu bếp | Phiếu bếp gồm bàn/mã đơn, món, số lượng, ghi chú | Tự động: `test_sales_tickets.py::test_ticket_carries_info` | ☐ Đạt ☐ Không đạt |
| TC-SALE-39 | FR-SALE-28 | Thu ngân/NV order | Lệnh in phiếu bếp thất bại | Bấm in lại nhiều lần | Không giới hạn số lần in lại, cảnh báo lỗi hiển thị khi in thất bại | Tự động: `test_sales_tickets.py::test_reprint_unlimited` | ☐ Đạt ☐ Không đạt |
| TC-SALE-40 | FR-SALE-29, FR-SET-08 | Thu ngân | Giao dịch QR 'Chờ xác nhận', chưa hết hạn | Chủ động hủy giao dịch QR | Chuyển 'Đã hủy', không tính doanh thu, cho tạo QR mới ngay sau đó, ghi audit log | Tự động: `test_sales_payments.py::test_cancel_qr` | ☐ Đạt ☐ Không đạt |

## 3. Module Kho (FR-INV-01 → FR-INV-12)

| Mã TC | FR | Vai trò | Tiền điều kiện | Các bước | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-INV-01 | FR-INV-01 | Nhân viên kho | Có nhà cung cấp | Ghi nhận phiếu nhập kho (nguyên liệu, số lượng, đơn giá, ngày nhập) | Tồn tăng đúng theo số lượng mua × hệ số quy đổi; sinh lô nguyên liệu | Tự động: `test_inventory_receipts.py::test_receipt_creates_lot_and_raises_stock_by_purchase_unit_times_factor` | ☐ Đạt ☐ Không đạt |
| TC-INV-02 | FR-INV-01 | Nhân viên kho | Nhà cung cấp không rõ | Ghi nhận phiếu nhập với mã nhà cung cấp không tồn tại | Bị từ chối | Tự động: `test_inventory_receipts.py::test_receipt_rejects_unknown_supplier` | ☐ Đạt ☐ Không đạt |
| TC-INV-03 | FR-INV-02, FR-SET-08 | Nhân viên kho | Phiếu nhập chưa phát sinh xuất kho liên quan | Sửa dòng phiếu nhập | Tồn được điều chỉnh lại tương ứng | Tự động: `test_inventory_receipts.py::test_edit_receipt_line_before_consumption_adjusts_stock` | ☐ Đạt ☐ Không đạt |
| TC-INV-04 | FR-INV-02 | Nhân viên kho | Lô nguyên liệu từ phiếu nhập đã bị tiêu thụ hết | Sửa dòng phiếu nhập đó | Bị từ chối | Tự động: `test_inventory_receipts.py::test_edit_receipt_refused_once_consumed` | ☐ Đạt ☐ Không đạt |
| TC-INV-05 | FR-INV-02, FR-SET-08 | Nhân viên kho | Phiếu nhập chưa có xuất kho liên quan | Hủy phiếu nhập | Tồn được hoàn trả lại (đảo ngược), ghi audit log | Tự động: `test_inventory_receipts.py::test_cancel_receipt_reverses_stock` | ☐ Đạt ☐ Không đạt |
| TC-INV-06 | FR-INV-02 | Nhân viên kho | Lô đã bị tiêu thụ hết | Hủy phiếu nhập | Bị từ chối | Tự động: `test_inventory_receipts.py::test_cancel_receipt_refused_once_lot_fully_consumed` | ☐ Đạt ☐ Không đạt |
| TC-INV-07 | FR-INV-02 | Nhân viên kho | Phiếu nhập đã bị hủy | Hủy lại phiếu đó lần nữa | Bị từ chối | Tự động: `test_inventory_receipts.py::test_cancel_receipt_twice_refused` | ☐ Đạt ☐ Không đạt |
| TC-INV-08 | FR-INV-02 (phân quyền) | Thu ngân | — | Thử tạo phiếu nhập kho | Bị từ chối (403) | Tự động: `test_inventory_receipts.py::test_cashier_cannot_create_receipt` | ☐ Đạt ☐ Không đạt |
| TC-INV-09 | FR-INV-03 | Hệ thống | Order submit lần đầu / thêm món / tăng số lượng | Kiểm tra tồn nguyên liệu sau thao tác | Trừ đúng theo công thức | Tự động: `test_sales_orders.py::test_submit_draws_stock` | ☐ Đạt ☐ Không đạt |
| TC-INV-10 | FR-INV-04 | Thu ngân/NV order | Dòng món 'Chờ làm' vừa bị hủy/giảm số lượng | Kiểm tra tồn nguyên liệu | Hoàn kho đúng số lượng đã trừ trước đó | Tự động: `test_sales_line_lifecycle.py::test_reducing_then_cancelling_returns_exactly_what_was_drawn` | ☐ Đạt ☐ Không đạt |
| TC-INV-11 | FR-INV-05 | Nhân viên kho | Có tồn đủ | Xuất kho thủ công cho hao hụt, kèm lý do | Ghi nhận thành công, tồn giảm đúng | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-INV-12 | FR-INV-06 | Nhân viên kho | Số lượng xuất > tồn khả dụng | Xuất kho thủ công vượt tồn | Bị từ chối, yêu cầu đối chiếu/kiểm kê lại | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-INV-13 | FR-INV-07 | Nhân viên kho | Nguyên liệu không có mức riêng | Đưa tồn xuống dưới mức mặc định hệ thống | Cảnh báo tồn tối thiểu được kích hoạt | Tự động: `test_catalog_ingredients.py::test_an_ingredient_without_its_own_threshold_uses_the_default` | ☐ Đạt ☐ Không đạt |
| TC-INV-14 | FR-INV-08 | Nhân viên kho | Có chênh lệch tồn thực tế và hệ thống | Lập phiếu kiểm kê, xác nhận | Tồn được ghi đè theo số kiểm kê, chênh lệch được ghi nhận | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-INV-15 | FR-INV-09 | Nhân viên kho | Tồn đã sai lệch do thao tác trước đó | Thử xuất kho thủ công tiếp mà chưa kiểm kê | Hệ thống dựa trên tồn hiện có; kiểm kê là kênh duy nhất để điều chỉnh sai lệch trước khi tiếp tục xuất | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-INV-16 | FR-INV-10 | Hệ thống | Tồn một nguyên liệu giảm dưới mức công thức yêu cầu | Kiểm tra danh sách món khả dụng | Món liên quan tự động ẩn ('Tự động ẩn do hết tồn kho'); hiện lại ngay khi kho đủ | Tự động: `test_catalog_tables.py::test_the_two_out_of_stock_causes_are_independent`, `test_sales_orders.py::test_rejected_when_out_of_stock` | ☐ Đạt ☐ Không đạt |
| TC-INV-17 | FR-INV-11 | Hệ thống | Hai order cùng submit tranh chấp một nguyên liệu còn ít tồn | Gửi đồng thời 2 request submit | Submit trước được trước, submit sau bị từ chối nếu không còn đủ tồn; không âm tồn | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-INV-18 | FR-INV-12 | Nhân viên kho, Quản lý | Có nhiều nguyên liệu | Xem danh sách tồn kho, lọc theo tên/trạng thái cảnh báo | Hiển thị đúng tên, đơn vị, tồn khả dụng, mức tối thiểu, trạng thái | Thủ công | ☐ Đạt ☐ Không đạt |

## 4. Module Báo cáo (FR-REP-01 → FR-REP-10)

| Mã TC | FR | Vai trò | Tiền điều kiện | Các bước | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-REP-01 | FR-REP-01 | Quản lý | Có hóa đơn đã tất toán trong tháng | Xem doanh thu theo BD/tuần/tháng | Tổng doanh thu đúng, chỉ tính hóa đơn đã tất toán | Tự động: `test_reports_revenue.py::test_revenue_counts_settled_invoices` | ☐ Đạt ☐ Không đạt |
| TC-REP-02 | FR-REP-01 | Quản lý | Nhiều bàn, nhiều hình thức thanh toán | Xem doanh thu phân theo bàn và theo hình thức thanh toán | Tổng theo từng chiều cộng lại đúng bằng tổng chung | Tự động: `test_reports_revenue.py::test_revenue_can_be_split_by_table_and_by_payment_method`, `test_the_split_by_table_sums_back_to_the_total` | ☐ Đạt ☐ Không đạt |
| TC-REP-03 | FR-REP-01 | Quản lý | Kỳ báo cáo không có dữ liệu | Xem báo cáo doanh thu kỳ rỗng | Trả về 0, không báo lỗi | Tự động: `test_reports_revenue.py::test_revenue_for_an_empty_period_is_zero_not_an_error` | ☐ Đạt ☐ Không đạt |
| TC-REP-04 | FR-REP-01, FR-REP-02 (phân quyền) | Thu ngân, Nhân viên kho | — | Truy cập báo cáo doanh thu | Bị từ chối (403) | Tự động: `test_reports_revenue.py::test_only_a_manager_may_read_revenue` | ☐ Đạt ☐ Không đạt |
| TC-REP-05 | FR-REP-02 | Quản lý | Có giao dịch QR 'Chờ đối soát' trong kỳ | Xem doanh thu kỳ đó | Giao dịch được tính tạm vào doanh thu | Tự động: `test_reports_revenue.py::test_a_transaction_awaiting_reconciliation_is_provisional_revenue` | ☐ Đạt ☐ Không đạt |
| TC-REP-06 | FR-REP-02 | Quản lý | Giao dịch trên vừa bị gắn cờ 'Tranh chấp' | Xem lại doanh thu kỳ đó | Giá trị giao dịch bị trừ lùi khỏi doanh thu thực nhận | Tự động: `test_reports_revenue.py::test_marking_a_dispute_subtracts_it_from_revenue` | ☐ Đạt ☐ Không đạt |
| TC-REP-07 | FR-REP-03 | Quản lý | Nhiều món có doanh số khác nhau | Xếp hạng theo số lượng và theo doanh thu | Hai cách sắp xếp cho thứ tự khác nhau đúng kỳ vọng | Tự động: `test_reports_rankings.py::test_the_ranking_can_be_sorted_by_quantity_or_by_revenue` | ☐ Đạt ☐ Không đạt |
| TC-REP-08 | FR-REP-03 | Quản lý | Có dòng món đã bị hủy | Xem xếp hạng món trong kỳ | Dòng món bị hủy không tính vào xếp hạng | Tự động: `test_reports_rankings.py::test_cancelled_lines_are_left_out_of_the_ranking` | ☐ Đạt ☐ Không đạt |
| TC-REP-09 | FR-REP-03 | Quản lý | Dữ liệu trải nhiều kỳ | Chọn khoảng thời gian cụ thể | Chỉ tính dữ liệu trong đúng khoảng đã chọn | Tự động: `test_reports_rankings.py::test_the_ranking_covers_the_selected_period_only` | ☐ Đạt ☐ Không đạt |
| TC-REP-10 | FR-REP-04 | Quản lý | Có doanh thu và giá vốn tháng | Xem biên lợi nhuận gộp toàn nhà hàng theo tháng | = Doanh thu − Giá vốn nguyên liệu tiêu hao | Tự động: `test_reports_margin.py::test_the_margin_is_revenue_minus_consumed_ingredients` | ☐ Đạt ☐ Không đạt |
| TC-REP-11 | FR-REP-05a | Quản lý | Công thức món đổi phiên bản giữa hai order | Tính giá vốn cho từng order | Dùng đúng phiên bản công thức có hiệu lực tại thời điểm order tạo, nhân đơn giá bình quân tháng | Tự động: `test_reports_margin.py::test_the_cost_uses_the_recipe_version_in_force_at_order_time` | ☐ Đạt ☐ Không đạt |
| TC-REP-12 | FR-REP-05b | Quản lý | Có phiếu xuất kho hao hụt trong tháng | Xem giá vốn tháng | Chi phí hao hụt/hư hỏng được cộng vào giá vốn | Tự động: `test_reports_margin.py::test_waste_is_part_of_the_cost` | ☐ Đạt ☐ Không đạt |
| TC-REP-13 | FR-REP-05 | Quản lý | Tháng có dòng xuất kho chưa hoàn tất tính giá vốn (job backfill chưa chạy) | Xem báo cáo giá vốn/hao hụt | Báo cáo gắn nhãn 'dữ liệu tạm tính' rõ ràng | Tự động: `test_reports_margin.py::test_a_month_with_uncosted_waste_rows_is_flagged_as_provisional`, `test_the_label_clears_once_the_backfill_has_run` | ☐ Đạt ☐ Không đạt |
| TC-REP-14 | FR-REP-06 | Quản lý | Có dữ liệu công thức + đơn giá | Xem chi phí nguyên liệu theo từng món | Không kèm hao hụt, không quy đổi thành biên lợi nhuận theo món, tổng cộng khớp giá vốn chung | Tự động: `test_reports_margin.py::test_the_per_dish_cost_excludes_waste`, `test_the_per_dish_cost_is_not_turned_into_a_margin`, `test_the_per_dish_costs_add_up_to_the_ingredient_cost` | ☐ Đạt ☐ Không đạt |
| TC-REP-15 | FR-REP-07 | Quản lý | Order trải nhiều khung giờ/ngày trong tuần | Xem phân bố theo khung giờ và theo ngày trong tuần | Gom nhóm đúng theo giờ nghiệp vụ và theo thứ | Tự động: `test_reports_rankings.py::test_hours_are_grouped_by_business_hour_and_by_weekday` | ☐ Đạt ☐ Không đạt |
| TC-REP-16 | FR-REP-07 | Quản lý | Order tạo sau nửa đêm nhưng trước 06:00 | Xem báo cáo khung giờ | Order được tính vào BD trước đó (BD 06:00→06:00), không tính vào ngày lịch mới | Tự động: `test_reports_rankings.py::test_a_late_night_order_belongs_to_the_previous_business_date` | ☐ Đạt ☐ Không đạt |
| TC-REP-17 | FR-REP-08 | Quản lý | Có dữ liệu 2 tháng khác nhau | So sánh doanh thu/chi phí giữa 2 khoảng thời gian | Hiển thị đúng % chênh lệch | Tự động: `test_reports_comparison.py::test_the_comparison_returns_the_percentage_change` | ☐ Đạt ☐ Không đạt |
| TC-REP-18 | FR-REP-08 | Quản lý | Một trong hai kỳ so sánh không có dữ liệu | So sánh với kỳ rỗng | Không chia cho 0, trả về kết quả hợp lệ | Tự động: `test_reports_comparison.py::test_comparing_against_an_empty_period_does_not_divide_by_zero` | ☐ Đạt ☐ Không đạt |
| TC-REP-19 | FR-REP-09 | Quản lý | Có dữ liệu báo cáo | Mở bất kỳ màn hình báo cáo nào | Hiển thị cả bảng số liệu và biểu đồ trực quan | Tự động (web): `revenue-chart.test.tsx::renders both a table and a chart` | ☐ Đạt ☐ Không đạt |
| TC-REP-20 | FR-REP-10 | Quản lý | Có order bị hủy toàn bộ trong kỳ | Xem báo cáo order bị hủy | Tổng giá trị, số lượng, lý do hiển thị đúng, tách biệt khỏi doanh thu | Tự động: `test_reports_comparison.py::test_the_cancelled_report_lists_totals_counts_and_reasons`, `test_the_cancelled_value_stays_out_of_revenue` | ☐ Đạt ☐ Không đạt |

## 5. Module Cài đặt (FR-SET-01 → FR-SET-09)

| Mã TC | FR | Vai trò | Tiền điều kiện | Các bước | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SET-01 | FR-SET-01, FR-SET-08 | Quản lý | — | Tạo tài khoản mới, gán vai trò | Tạo thành công, ghi audit log | Tự động: `test_settings_accounts.py::test_account_creation_is_audited` | ☐ Đạt ☐ Không đạt |
| TC-SET-02 | FR-SET-01 (phân quyền) | Thu ngân, Nhân viên kho | — | Thử tạo tài khoản | Bị từ chối (403) | Tự động: `test_settings_accounts.py::test_only_a_manager_may_create_accounts` | ☐ Đạt ☐ Không đạt |
| TC-SET-03 | FR-SET-01 | Quản lý | — | Tạo tài khoản gán 2 vai trò hoặc không vai trò | Bị từ chối — mỗi tài khoản đúng một trong ba vai trò | Tự động: `test_settings_accounts.py::test_a_user_is_given_exactly_one_of_the_three_roles` | ☐ Đạt ☐ Không đạt |
| TC-SET-04 | FR-SET-01 | Quản lý | Tài khoản đang hoạt động | Khóa tài khoản | Tài khoản không đăng nhập được nữa | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-05 | FR-SET-02 | Mọi vai trò | Tài khoản đang hoạt động | Đăng nhập bằng đúng tài khoản/mật khẩu | Nhận được access token | Tự động: `test_settings_auth.py::test_login_returns_a_token_for_an_active_account` | ☐ Đạt ☐ Không đạt |
| TC-SET-06 | FR-SET-02 | Mọi vai trò | Tài khoản bị khóa | Đăng nhập | Bị từ chối | Tự động: `test_settings_auth.py::test_locked_account_cannot_log_in` | ☐ Đạt ☐ Không đạt |
| TC-SET-07 | FR-SET-02, NFR-04 | Mọi vai trò | — | Đăng nhập sai mật khẩu | Bị từ chối, thông báo không tiết lộ trường nào sai (username hay mật khẩu) | Tự động: `test_settings_auth.py::test_wrong_password_is_rejected_without_revealing_which_field_failed` | ☐ Đạt ☐ Không đạt |
| TC-SET-08 | FR-SET-02 | Mọi vai trò | Đã đăng nhập | Tự đổi mật khẩu | Đổi thành công, không ghi vào audit log rủi ro cao | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-09 | FR-SET-02, FR-SET-08 | Quản lý | Nhân viên quên mật khẩu | Quản lý đặt lại mật khẩu hộ | Đặt lại thành công, ghi audit log | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-10 | FR-SET-03 | Cả ba vai trò | — | Đối chiếu với Bảng 33 (§3.4.2) | Từng vai trò chỉ thao tác được đúng phạm vi — xem mục "6. Kiểm thử phân quyền" | Tự động (nhiều file, xem mục 6) | ☐ Đạt ☐ Không đạt |
| TC-SET-11 | FR-SET-04 | Quản lý | — | Cấu hình tên, địa chỉ, mẫu hóa đơn nhà hàng | Lưu thành công, áp dụng cho hóa đơn in sau đó | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-12 | FR-SET-05 | Quản lý | — | Cấu hình mức tồn tối thiểu mặc định | Lưu thành công, áp dụng cho nguyên liệu chưa có mức riêng | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-12b | NFR (cấu hình hệ thống chỉ đọc field bảo vệ) | Thu ngân, Nhân viên kho | — | Đọc cấu hình hệ thống | Bị từ chối (chỉ Quản lý) | Tự động: `test_settings_config.py::test_a_non_manager_cannot_read_the_config` | ☐ Đạt ☐ Không đạt |
| TC-SET-12c | Ràng buộc Business Date cố định | Quản lý | — | Thử sửa mốc bắt đầu Business Date (06:00) qua API | Bị từ chối — không sửa được qua API | Tự động: `test_settings_config.py::test_the_business_day_start_cannot_be_edited_from_the_api` | ☐ Đạt ☐ Không đạt |
| TC-SET-13 | FR-SET-06, FR-SET-08 | Quản lý | — | Xuất bản sao dữ liệu thủ công | Xuất thành công, ghi audit log | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-14 | FR-SET-07, FR-SET-08 | Quản lý/Hệ thống | Có bản sao lưu | Phục hồi dữ liệu (thủ công hoặc theo lịch) | Phục hồi thành công, ghi audit log | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-15 | FR-SET-08 | Quản lý | Thực hiện một thao tác rủi ro cao (vd. hủy toàn bộ order) | Xem audit log | Bản ghi xuất hiện đúng loại thao tác | Tự động: gián tiếp qua `latest_audit()` trong `tests/helpers.py`, dùng ở `test_catalog_dishes.py`, `test_catalog_prices.py`, `test_catalog_recipes.py`, `test_catalog_ingredients.py`, `test_settings_accounts.py` | ☐ Đạt ☐ Không đạt |
| TC-SET-16 | FR-SET-09 | Quản lý | Audit log có bản ghi | Xem chi tiết một bản ghi | Có đủ người thực hiện, thời điểm, loại thao tác, dữ liệu trước/sau | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-SET-17 | FR-SET-09 (phân quyền) | Thu ngân, Nhân viên kho | — | Truy cập audit log | Bị từ chối (403) | Tự động: `test_settings_audit_log.py::test_only_a_manager_can_read_the_audit_log` | ☐ Đạt ☐ Không đạt |
| TC-SET-18 | NFR-07 | Quản lý | Audit log có bản ghi | Thử sửa/xóa một bản ghi audit log qua API | Không có endpoint nào cho phép sửa/xóa | Tự động: `test_settings_audit_log.py::test_the_log_cannot_be_edited_or_deleted` | ☐ Đạt ☐ Không đạt |

## 6. Kiểm thử phân quyền / bảo mật dữ liệu theo vai trò (Bảng 32, 33 — §3.4)

Mỗi dòng đối chiếu trực tiếp một ô "Không" hoặc "Chỉ xem" trong Bảng 33 với kỳ vọng **403 Forbidden**
(hoặc dữ liệu bị lọc/ẩn với thao tác đọc "chỉ xem"), và một ô "Có" với kỳ vọng thao tác thành công.

| Mã TC | Vai trò | Chức năng bị giới hạn (Bảng 33) | Bước kiểm thử | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- |
| TC-AUTH-01 | Thu ngân/NV order | Sửa/xóa món ăn, nhóm món, công thức, giá | Gọi API sửa món ăn | 403 | Tự động: `test_catalog_ingredients.py::test_warehouse_staff_may_manage_ingredients_but_not_dishes` (đối xứng cho Thu ngân — xác nhận qua review code `router.py` catalog) | ☐ Đạt ☐ Không đạt |
| TC-AUTH-02 | Nhân viên kho | Sửa/xóa món ăn, nhóm món, công thức, giá | Gọi API sửa món ăn | 403 | Tự động: `test_catalog_ingredients.py::test_warehouse_staff_may_manage_ingredients_but_not_dishes` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-03 | Thu ngân/NV order | Quản lý nguyên liệu, nhà cung cấp (FR-CAT-12–16) | Gọi API tạo nguyên liệu | 403 | Thủ công (đối chiếu quyền `router.py`) | ☐ Đạt ☐ Không đạt |
| TC-AUTH-04 | Nhân viên kho | Quản lý nguyên liệu, nhà cung cấp | Gọi API tạo/sửa nguyên liệu | Thành công | Tự động: `test_catalog_ingredients.py::test_warehouse_staff_may_manage_ingredients_but_not_dishes` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-05 | Thu ngân/NV order | Sơ đồ bàn: chỉ xem trạng thái, không sửa/xóa | Gọi API sửa/xóa bàn | Xem: thành công. Sửa/xóa: 403 | Tự động: `test_catalog_tables.py::test_the_cashier_sees_the_floor_plan_but_cannot_edit_it` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-06 | Nhân viên kho | Lập order, thanh toán, in phiếu bếp | Gọi API tạo order / in lại hóa đơn | 403 | Tự động: `test_sales_tickets.py::test_warehouse_cannot_reprint` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-07 | Thu ngân/NV order | Hủy toàn bộ order (chỉ Quản lý) | Gọi API hủy toàn bộ order | 403 | Tự động: `test_sales_line_lifecycle.py::test_only_manager_cancel_whole` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-08 | Thu ngân | Xác nhận kết quả đối soát (chỉ Quản lý) | Gọi API xác nhận đối soát | 403 | Tự động: `test_sales_reconciliation.py::test_only_manager_resolve` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-09 | Thu ngân/NV order | Ghi nhận/sửa/hủy phiếu nhập kho (FR-INV-01–02) | Gọi API tạo phiếu nhập kho | 403 | Tự động: `test_inventory_receipts.py::test_cashier_cannot_create_receipt` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-10 | Thu ngân/NV order | Xuất kho thủ công, kiểm kê (FR-INV-05–06, 08–09) | Gọi API xuất kho thủ công | 403 | Thủ công (đối chiếu quyền `router.py` inventory) | ☐ Đạt ☐ Không đạt |
| TC-AUTH-11 | Thu ngân/NV order | Xem danh sách tồn kho — chỉ xem cảnh báo hết món, không xem chi tiết kho | Gọi API danh sách tồn kho đầy đủ | Bị lọc/từ chối trường chi tiết (giá nhập, số lô) | Thủ công | ☐ Đạt ☐ Không đạt |
| TC-AUTH-12 | Thu ngân, Nhân viên kho | Báo cáo doanh thu/giá vốn/lợi nhuận (chỉ Quản lý) | Gọi API báo cáo doanh thu | 403 | Tự động: `test_reports_revenue.py::test_only_a_manager_may_read_revenue` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-13 | Thu ngân, Nhân viên kho | Quản lý tài khoản, gán vai trò (chỉ Quản lý) | Gọi API tạo tài khoản | 403 | Tự động: `test_settings_accounts.py::test_only_a_manager_may_create_accounts` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-14 | Thu ngân, Nhân viên kho | Cấu hình hệ thống (chỉ Quản lý) | Gọi API đọc/sửa cấu hình | 403 | Tự động: `test_settings_config.py::test_a_non_manager_cannot_read_the_config` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-15 | Thu ngân, Nhân viên kho | Xem audit log (chỉ Quản lý) | Gọi API đọc audit log | 403 | Tự động: `test_settings_audit_log.py::test_only_a_manager_can_read_the_audit_log` | ☐ Đạt ☐ Không đạt |
| TC-AUTH-16 | Quản lý | Kế thừa toàn bộ quyền Thu ngân + Nhân viên kho | Gọi lần lượt: tạo order, thanh toán, tạo phiếu nhập kho, xuất kho thủ công | Toàn bộ thành công, đúng người thực hiện được ghi vào audit log | Thủ công (không có test tự động xác nhận Quản lý dùng được toàn bộ endpoint của cả 2 vai trò trong 1 kịch bản) | ☐ Đạt ☐ Không đạt |

## 7. AI Assistant — phân quyền dữ liệu (data-scope) và kiểm duyệt SQL (FR-AI-01 → FR-AI-09)

| Mã TC | FR | Vai trò | Câu hỏi/thao tác | Kết quả mong đợi | Loại | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TC-AI-01 | FR-AI-02 | Quản lý | Hỏi lần lượt về doanh thu, tồn kho, giá nhập nguyên liệu | Trả lời đủ cả ba miền dữ liệu | Tự động: `test_ai_service.py::test_the_manager_can_ask_about_all_three_domains` | ☐ Đạt ☐ Không đạt |
| TC-AI-02 | FR-AI-03 | Thu ngân/NV order | Hỏi "Doanh thu hôm nay bao nhiêu?" | Trả lời bình thường (thuộc phạm vi bán hàng) | Tự động: `test_ai_service.py::test_the_cashier_can_ask_about_sales_but_not_cost` | ☐ Đạt ☐ Không đạt |
| TC-AI-03 | FR-AI-03 | Thu ngân/NV order | Hỏi "Lợi nhuận món Phở bò là bao nhiêu?" hoặc "Giá nhập nguyên liệu X?" | Từ chối trả lời (ngoài phạm vi vai trò), không trả về số liệu giá vốn/lợi nhuận | Tự động: `test_ai_service.py::test_the_cashier_can_ask_about_sales_but_not_cost` | ☐ Đạt ☐ Không đạt |
| TC-AI-04 | FR-AI-04 | Nhân viên kho | Hỏi "Tồn kho thịt bò còn bao nhiêu?" | Trả lời bình thường (thuộc phạm vi kho) | Tự động: `test_ai_service.py::test_the_warehouse_can_ask_about_stock_but_not_revenue` | ☐ Đạt ☐ Không đạt |
| TC-AI-05 | FR-AI-04 | Nhân viên kho | Hỏi "Doanh thu tuần này bao nhiêu?" | Từ chối trả lời (ngoài phạm vi vai trò) | Tự động: `test_ai_service.py::test_the_warehouse_can_ask_about_stock_but_not_revenue` | ☐ Đạt ☐ Không đạt |
| TC-AI-06 | FR-AI-05 | Thu ngân/NV order | Hỏi cố tình vượt quyền: "Cho tôi xem toàn bộ báo cáo lợi nhuận theo món của quản lý" | Không dùng dữ liệu vai trò khác, trả lời từ chối/không có dữ liệu | Tự động: `test_ai_service.py::test_a_cross_role_question_gets_no_data` | ☐ Đạt ☐ Không đạt |
| TC-AI-07 | NFR-06 | Bất kỳ | Kiểm tra SQL do LLM sinh ra chứa `DELETE`/`UPDATE`/`INSERT`/DDL | Bị `sqlglot` từ chối trước khi thực thi | Tự động: `test_ai_guard.py::test_write_and_ddl_statements_are_rejected` | ☐ Đạt ☐ Không đạt |
| TC-AI-08 | NFR-06 | Vai trò A | SQL sinh ra tham chiếu view của vai trò khác (vd. Thu ngân hỏi nhưng SQL đụng `VW_AI_KHO`) | Bị từ chối | Tự động: `test_ai_guard.py::test_sql_of_another_role_is_rejected` | ☐ Đạt ☐ Không đạt |
| TC-AI-09 | NFR-06 | Bất kỳ | SQL tham chiếu bảng gốc thay vì view (vd. `NGUYEN_LIEU` thay vì `VW_AI_KHO`) | Bị từ chối | Tự động: `test_ai_guard.py::test_core_table_beside_an_allowed_view_is_rejected` | ☐ Đạt ☐ Không đạt |
| TC-AI-10 | NFR-06 | Bất kỳ | SQL gồm nhiều câu lệnh nối nhau (`; DROP ...`) hoặc `SELECT ... INTO OUTFILE` | Bị từ chối | Tự động: `test_ai_guard.py::test_multiple_statements_are_rejected`, `test_into_outfile_is_rejected` | ☐ Đạt ☐ Không đạt |
| TC-AI-11 | NFR-06 | Bất kỳ | SQL gọi hàm nguy hiểm (`LOAD_FILE`, `SLEEP`, ...) | Bị từ chối | Tự động: `test_ai_guard.py::test_dangerous_functions_are_rejected` | ☐ Đạt ☐ Không đạt |
| TC-AI-12 | NFR-06 | Bất kỳ | SQL không hợp lệ ở lần sinh thứ nhất | Hệ thống thử sinh lại lần 2 | Tự động: `test_ai_generator.py::test_the_model_gets_a_second_attempt_after_a_bad_query` | ☐ Đạt ☐ Không đạt |
| TC-AI-13 | NFR-06 | Bất kỳ | SQL vẫn lỗi sau lần thử thứ hai | Kết thúc với trạng thái phù hợp, không thử lần 3 | Tự động: `test_ai_generator.py::test_a_third_attempt_never_happens` | ☐ Đạt ☐ Không đạt |
| TC-AI-14 | NFR-06 | Bất kỳ | Đo thời gian thực thi câu SQL hợp lệ trên CSDL thật | ≤ 3 giây | Tự động: `test_ai_executor.py::test_the_statement_timeout_is_applied` | ☐ Đạt ☐ Không đạt |
| TC-AI-15 | NFR-06, NFR-12 | Từng vai trò | Kiểm tra tài khoản CSDL dùng khi thực thi | Mỗi vai trò dùng đúng tài khoản chỉ-đọc riêng, không dùng chung; không có quyền ghi | Tự động: `test_ai_accounts.py::test_roles_do_not_share_a_connection_string`, `test_ai_executor.py::test_the_account_is_never_reused_across_roles`, `test_ai_views.py::test_grants_per_role_on_mysql` | ☐ Đạt ☐ Không đạt |
| TC-AI-16 | FR-AI-06 | Bất kỳ | Hỏi mơ hồ, không xác định được món/nguyên liệu/khoảng thời gian (vd. "món đó bán chạy không?") | Yêu cầu người dùng làm rõ, không đoán bừa | Tự động: `test_ai_generator.py::test_an_out_of_scope_question_asks_for_clarification`, `test_ai_service.py::test_a_vague_question_asks_for_clarification` | ☐ Đạt ☐ Không đạt |
| TC-AI-17 | FR-AI-07 | Bất kỳ | Hỏi dữ liệu biến động theo thời gian / so sánh nhóm / cơ cấu tỷ trọng | Chọn đúng loại biểu đồ: line / bar / doughnut tương ứng | Tự động: `test_ai_interpreter.py::test_a_time_series_becomes_a_line_chart`, `test_a_comparison_between_groups_becomes_a_bar_chart`, `test_a_share_of_a_whole_becomes_a_doughnut_chart` | ☐ Đạt ☐ Không đạt |
| TC-AI-18 | FR-AI-07 | Bất kỳ | Kết quả không khớp 3 dạng biểu đồ trên | Chỉ hiển thị bảng, không có chart | Tự động: `test_ai_interpreter.py::test_two_columns_that_are_not_a_series_get_no_chart`, `test_a_single_number_gets_no_chart` | ☐ Đạt ☐ Không đạt |
| TC-AI-19 | FR-AI-07 | Bất kỳ | Đặt bất kỳ câu hỏi hợp lệ nào | Câu trả lời tiếng Việt, kèm bảng số liệu gốc và ghi chú phạm vi dữ liệu | Tự động: `test_ai_interpreter.py::test_the_answer_is_vietnamese_and_carries_the_scope_note`, `test_the_scope_note_differs_per_role` | ☐ Đạt ☐ Không đạt |
| TC-AI-20 | FR-AI-08 | Bất kỳ | Nhận được câu trả lời | Mở mục "Xem chi tiết" | Mặc định thu gọn; mở ra thấy SQL và thông tin kỹ thuật | Tự động (web): `chat-panel.test.tsx::keeps the SQL detail collapsed by default` | ☐ Đạt ☐ Không đạt |
| TC-AI-21 | FR-AI-09 | Bất kỳ | Câu hỏi không tạo được câu trả lời hợp lệ (SQL lỗi cả 2 lần) | Thông báo rõ ràng, gợi ý diễn đạt lại, không im lặng/không trả sai | Tự động: `test_ai_service.py::test_a_refusal_is_recorded_and_explained` | ☐ Đạt ☐ Không đạt |
| TC-AI-22 | NFR-02 | Bất kỳ | Đặt một câu hỏi thông thường | Toàn bộ chuỗi xử lý phản hồi dưới 8 giây | Tự động: `test_ai_service.py::test_a_slow_turn_is_cut_off_at_the_response_budget` | ☐ Đạt ☐ Không đạt |
| TC-AI-23 | NFR-14 | Bất kỳ | Kiểm tra mọi thông báo hệ thống trong luồng chat (kể cả lỗi) | Toàn bộ hiển thị tiếng Việt | Tự động: `test_ai_service.py::test_every_message_shown_to_the_user_is_vietnamese` | ☐ Đạt ☐ Không đạt |
| TC-AI-24 | FR-AI-01 | Từng vai trò | Mở phiên chat AI | Phiên gắn đúng view/tài khoản của vai trò đăng nhập; phiên đầu tiên tạo mới, các lượt sau dùng lại cùng phiên | Tự động: `test_ai_service.py::test_the_session_is_created_on_the_first_turn_and_reused_after`, `test_each_role_talks_to_its_own_view` | ☐ Đạt ☐ Không đạt |
| TC-AI-25 | NFR-16 | Bất kỳ | Hỏi lại đúng một câu hỏi đã hỏi trước đó | Trả lời từ cache, không gọi lại LLM | Tự động: `test_ai_generator.py::test_a_repeated_question_is_served_from_cache`, `test_the_cache_does_not_leak_across_roles` | ☐ Đạt ☐ Không đạt |
| TC-AI-26 | NFR-16 | Một vai trò | Vượt hạn mức câu hỏi/ngày | Từ chối gọi thêm LLM cho tới khi hạn mức reset | Tự động: `test_ai_generator.py::test_the_daily_quota_stops_further_calls` | ☐ Đạt ☐ Không đạt |

---

### Ghi chú độ phủ FR

Toàn bộ FR-CAT (28), FR-SALE (29), FR-INV (12), FR-REP (10), FR-SET (9) và FR-AI (9) đều có ít nhất một
test case ở trên. Các trường hợp đánh dấu "Thủ công" là những thao tác gắn với phần cứng thật (máy in
nhiệt, cổng thanh toán QR thật), thao tác đồng thời khó dựng tất định trong test tự động (tranh chấp tồn
kho thực), hoặc UI thuần túy chưa có test tương ứng tại thời điểm viết tài liệu này — cần chạy tay theo
đúng bước mô tả và tick kết quả.
