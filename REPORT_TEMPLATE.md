# Báo cáo LAB 17 — Data Pipeline Engineering

**Họ tên:** …  **Lớp:** AICB-P2T2  **Ngày:** …

---

## 0 · Kết quả `make verify`

<details>
<summary>Dán nguyên output ba lần chạy vào đây</summary>

```
(dán output make verify)
```

</details>

Tổng kết: **4 / 4 tiêu chí đạt**

---

## 1 · Kích thước bảng training tăng sau mỗi lần chạy

| | |
|---|---|
| **Triệu chứng** | Sau khi `make reset`, chạy `make pipeline` nhiều lần làm `gold_training_set` tăng số hàng. `silver_tickets` vẫn có 12.480 ticket duy nhất, nhưng `gold_training_set` có 38.750 hàng và nhiều `ticket_id` bị lặp tới 4 lần. |
| **Nguyên nhân** | `gold_training_set` là incremental model nhưng không khai báo `unique_key`, nên dbt sinh thao tác ghi thêm (`INSERT/append`) thay vì cập nhật theo key. Khi chạy lại cùng dữ liệu hoặc cùng partition vận hành, hàng cũ không bị thay thế mà bị ghi thêm. Đây là bảng entity có grain 1 hàng / 1 ticket, nên append không phù hợp. |
| **Cách khắc phục** | Trong `dbt/models/gold/gold_training_set.sql`, thêm `unique_key = 'ticket_id'` và `incremental_strategy = 'merge'` để mỗi ticket được ghi đè theo khoá tự nhiên. Trong `dags/ai_training_pipeline.py`, đặt `catchup=False` và `max_active_runs=1` để giảm rủi ro nhiều DAG run ghi đồng thời hoặc chạy bù ngoài ý muốn. |
| **Bằng chứng** | trước: 38.750 hàng, `gold_training_set: 1 hàng / 1 ticket` fail · sau: 12.480 hàng, không lặp ticket · checksum 3 lượt: `8dd7c98653`, `8dd7c98653`, `8dd7c98653` |

---

## 2 · Bảng đặc trưng theo ngày thiếu hàng ở các ngày quá khứ

| | |
|---|---|
| **Triệu chứng** | `gold_feature_daily` chỉ có 8.645 hàng trong khi kỳ vọng là 9.100 cặp `(event_date, customer_id)`. Các cặp bị thiếu nằm ở ngày cũ do event tới kho muộn sau ngày phát sinh. |
| **P99 độ trễ đo được** | **2,73 ngày** *(bắt buộc)* |
| **Lookback đã chọn** | 3 ngày — vì P99 là 2,73 ngày và max quan sát được khoảng 2,94 ngày, nên cửa sổ 3 ngày phủ được dữ liệu tới muộn trong tập này mà không cần quét lại toàn bộ lịch sử. |
| **Nguyên nhân** | Điều kiện incremental cũ chỉ lấy `event_date > max(event_date)` trong bảng đích. Khi một event của ngày cũ, ví dụ 2026-08-12, tới kho vào 2026-08-15, `max(event_date)` trong target đã tiến tới ngày mới hơn nên event đó không bao giờ được tính lại vào gold. |
| **Cách khắc phục** | Trong `dbt/models/gold/gold_feature_daily.sql`, đổi incremental filter sang lookback 3 ngày: `event_date >= max(event_date) - interval 3 day`. Đồng thời thêm `unique_key = ['event_date', 'customer_id']` và `incremental_strategy = 'merge'` để các cặp được tính lại sẽ thay thế bản cũ thay vì ghi thêm. |
| **Bằng chứng** | trước: 8.645 hàng · sau: 9.100 hàng · checksum 3 lượt: `3db448685c`, `3db448685c`, `3db448685c` |

Vì sao chọn P99 làm căn cứ thay vì `max`? Chi phí của mỗi lựa chọn là gì?

> P99 phản ánh độ trễ phổ biến ở phần đuôi phân phối nhưng tránh để một vài outlier quyết định chi phí vận hành lâu dài. Chọn theo `max` sẽ an toàn hơn cho mọi bản ghi cực đoan trong dữ liệu đã thấy, nhưng mỗi ngày lookback tăng thêm đều làm mọi lượt chạy sau này phải đọc và merge thêm nhiều partition cũ. Vì vậy chọn 3 ngày dựa trên P99 2,73 ngày là cân bằng giữa độ đầy đủ và chi phí xử lý.

---

## 3 · Kiểu dữ liệu cột priority thay đổi giữa chu kỳ

| | |
|---|---|
| **Triệu chứng** | `silver_tickets.priority` có 6.606 hàng sai: nhiều giá trị `NULL`, đồng thời có các giá trị ngoài contract như `0`, `5`, `-1`. `quarantine_tickets` rỗng dù kỳ vọng có 312 bản ghi lỗi. |
| **Nguyên nhân** | Source đổi cách biểu diễn priority từ số sang nhãn chữ từ giữa chu kỳ. Macro cũ chỉ `try_cast(priority_raw as integer)`, nên nhãn hợp lệ như `urgent/high/medium/low` bị biến thành `NULL`, trong khi các số ngoài miền như `0`, `5`, `-1` lại được chấp nhận vì cast được sang integer. |
| **Ba nhóm giá trị `priority` và cách xử lý từng nhóm** | Nhóm số hợp lệ `1`, `2`, `3`, `4`: giữ nguyên. Nhóm nhãn hợp lệ `urgent`, `high`, `medium`, `low`: map lần lượt về `1`, `2`, `3`, `4`. Nhóm lỗi thật `P1`, `P2`, `unknown`, `0`, `5`, `-1`, chuỗi rỗng, `NULL`: trả về `NULL` và đưa vào `quarantine_tickets`. |
| **Cách khắc phục** | Trong `dbt/macros/normalize_priority.sql`, thay `try_cast` bằng `CASE` xử lý đủ ba nhóm. Trong `dbt/models/silver/silver_tickets.sql`, chuẩn hoá rồi lọc `priority_clean is not null` trước khi `row_number`, để chỉ loại bản ghi CDC lỗi chứ không làm mất cả ticket. Trong `dbt/models/silver/quarantine_tickets.sql`, chọn các row mà macro trả `NULL`. Trong `dbt/models/silver/schema.yml`, bật contract và thêm test `not_null`, `accepted_values` cho priority. |
| **Bằng chứng** | `quarantine_tickets` = 312 hàng · `dbt test` 11/11 pass · `silver_tickets.priority ∈ 1..4, không NULL`: sạch · checksum quarantine 3 lượt: `ebb89036fb`, `ebb89036fb`, `ebb89036fb` |

Câu hỏi thiết kế: nên chặn ở tầng Bronze hay Silver? Vì sao **không** để
pipeline dừng khi gặp bản ghi lỗi?

> Nên giữ Bronze là vùng lưu dữ liệu thô để còn đủ bằng chứng điều tra sự cố: source gửi gì, gửi lúc nào, ảnh hưởng ticket nào. Việc áp contract nên làm ở Silver: dữ liệu hợp lệ đi tiếp, dữ liệu lỗi được tách sang quarantine. Không nên để `dbt test` fail và dừng cả DAG cho vài trăm row lỗi, vì như vậy hơn 130.000 event và 31.200 chunk hợp lệ cũng bị chặn; quarantine cho phép pipeline tiếp tục phục vụ dữ liệu tốt trong khi người trực xử lý phần lỗi.

---

## 4 · *(mở rộng, không bắt buộc)* Bài trong EXTRA.md

| | |
|---|---|
| **Bài đã làm** | A và B |
| **Nguyên nhân** | Bài A: dashboard đọc 5.000 file Parquet nhỏ không partition, nên DuckDB phải mở toàn bộ file trước khi lọc; điều kiện `strftime(event_time, ...)` cũng làm predicate theo ngày không sargable. Bài B: consumer commit offset trước khi ghi dữ liệu, nên nếu tiến trình chết giữa batch thì offset đã dịch nhưng batch chưa được ghi, dẫn tới mất dữ liệu. |
| **Cách khắc phục** | Bài A: trong `tools/compact.py`, ghi lại dataset sang `data/gold_events_v2`, partition theo `event_date`, sort theo `event_date, customer_name, event_time`, row group size 2048; trong `queries/dashboard.sql`, đọc dataset mới với `hive_partitioning = true` và lọc bằng `event_date = date '2026-08-09'` cùng range trên `event_time`. Bài B: trong `ingest/consumer.py`, đổi thứ tự thành ghi batch trước rồi mới commit offset, thêm primary key `event_id`, và ghi bằng `ON CONFLICT (event_id) DO UPDATE` để replay batch không tạo trùng mà vẫn cập nhật được nội dung mới nhất. |
| **Bằng chứng** | Bài A: rows scanned `5.000.000 → 136.934` giảm 36,5×; files `5.000 → 14`; rows on disk giữ `130.683`; result hash giữ nguyên `4379e4c5d9f3`. Bài B: `make crash-test` đạt, sau restart có `20.000` hàng / `20.000` event_id khác nhau, không mất, không trùng, `C == A`. |

---

## 5 · Tổng kết

| Nhiệm vụ | Khi tiếp nhận một hệ thống chưa quen, tôi sẽ kiểm tra điều này trước tiên |
|---|---|
| 1 | Với incremental model, kiểm tra grain của bảng, khoá tự nhiên, `unique_key`, `incremental_strategy`, và cách hệ thống xử lý khi chạy lại cùng một ngày dữ liệu. |
| 2 | Với bảng tổng hợp theo ngày, kiểm tra độ trễ giữa event time và ingest time, điều kiện incremental filter, lookback window, và khoá merge của đúng grain tổng hợp. |
| 3 | Với cột có contract, kiểm tra cả kiểu dữ liệu lẫn miền giá trị, phân biệt schema evolution hợp lệ với dữ liệu lỗi thật, và thiết kế quarantine để không làm dừng toàn bộ pipeline. |
