# RUBRIC — LAB 17 · thang 100 điểm

Phần lớn điểm được chấm **tự động** bằng `make verify`, `make explain` và
`make crash-test`. Phần còn lại chấm bằng mắt trên báo cáo.

```bash
make verify        # A + B + C
make explain       # bài mở rộng A (cần make seed-extra)
make crash-test    # bài mở rộng B
```

---

## Tổng quan

| Mục | Nội dung | Điểm |
|---|---|---|
| **A** | Tính ổn định — chạy ba lần ra checksum giống hệt nhau | **30** |
| **B** | Tính đúng — số hàng ba bảng Gold khớp `expected/` | **30** |
| **C** | Chất lượng dữ liệu — contract, test, quarantine | **20** |
| **D** | Báo cáo — nêu đúng **nguyên nhân** | **20** |
| **+** | *(thưởng)* mỗi bài trong `EXTRA.md` | **+5** |
| — | *(trừ)* xem mục "Trừ điểm" | **−** |

Tối đa **110/100**.

---

## A · Tính ổn định — 30 điểm

Nguồn: cột `ỔN ĐỊNH` và bảng `CHECKSUM từng lượt` của `make verify`.

| | Điểm |
|---|---|
| `gold_training_set` cho cùng checksum ở cả ba lượt | 12 |
| `gold_feature_daily` cho cùng checksum ở cả ba lượt | 12 |
| `gold_doc_chunks` cho cùng checksum ở cả ba lượt *(nhóm đối chứng: sai lệch ở bảng này nghĩa là một thành phần vốn hoạt động đúng đã bị ảnh hưởng)* | 3 |
| `quarantine_tickets` cho cùng checksum ở cả ba lượt | 3 |

> Điểm mục A **không** phụ thuộc số hàng có đúng hay không. Một bảng có thể ổn
> định mà vẫn sai — và ngược lại. Đó là lý do A và B tách riêng.

## B · Tính đúng — 30 điểm

Nguồn: cột `SỐ HÀNG` so với `expected/`.

| | Kỳ vọng | Điểm |
|---|---|---|
| `gold_training_set` | 12.480 | 12 |
| `gold_feature_daily` | 9.100 | 12 |
| `gold_doc_chunks` | 31.200 | 3 |
| `gold_training_set`: 1 hàng / 1 `ticket_id` (không lặp) | — | 3 |

Không có điểm từng phần cho kết quả xấp xỉ: trong vận hành thực tế, một
sai lệch không đo được là một sai lệch không kiểm soát được.

## C · Chất lượng dữ liệu — 20 điểm

| | Điểm |
|---|---|
| `contract: enforced: true` trên `silver_tickets` và `dbt run` vẫn chạy | 5 |
| `dbt test` pass **và** có thêm test mới so với bản gốc (bản gốc có 9 test) | 5 |
| `quarantine_tickets` đúng **312** hàng, đúng grain (1 hàng / 1 bản ghi CDC) | 5 |
| `silver_tickets.priority` không NULL và luôn ∈ 1..4 | 3 |
| `silver_tickets` vẫn đủ **12.480** ticket *(loại bản ghi, không loại ticket)* | 2 |

**Trừ trong mục C:** `quarantine_tickets` vượt 1.000 hàng — dấu hiệu đã quarantine
nhầm nhóm nhãn chuỗi hợp lệ — mất toàn bộ 4 điểm của hạng mục quarantine, kể cả
khi `dbt test` pass.

## D · Báo cáo — 20 điểm

Ba nhiệm vụ, mỗi nhiệm vụ **6 điểm** cho mục **Nguyên nhân**, cộng **2 điểm**
cho con số P99 ở nhiệm vụ 2.

| Chất lượng | Điểm/nhiệm vụ |
|---|---|
| Nêu đúng **cơ chế** gây lỗi, đủ cụ thể để người đọc phòng tránh được trường hợp tương tự | 6 |
| Đúng nhưng chung chung ("model cấu hình sai") | 3 |
| Chỉ mô tả cách sửa ("tôi đổi một tham số trong `config()`") | 1 |
| Không có / sai | 0 |

Ví dụ so sánh — lấy một sự cố **không** có trong lab này, để bạn thấy khác biệt
mà không bị lộ đáp án: *"job gửi email nhắc hạn gửi trùng cho một số khách"*.

> ✗ *1đ* — "Tôi thêm một bảng `sent_log` và kiểm tra trước khi gửi."
>
> Đây là **cách sửa**. Người đọc không học được gì: lần sau gặp job khác họ
> vẫn mắc lại.
>
> ✓ *6đ* — "Job quét theo `where due_date = today` rồi gửi, nhưng không ghi
> lại dấu vết là đã gửi. Retry của scheduler khi timeout mạng vì thế là một
> lần gửi mới hoàn toàn — bản thân hành động gửi không idempotent, nên **mọi**
> cơ chế retry ở tầng trên đều biến thành cơ chế nhân bản."

## + · Thưởng — mỗi bài 5 điểm

Hai bài trong [EXTRA.md](EXTRA.md), cần chạy `make seed-extra` trước:

| | Điểm |
|---|---|
| **Bài A** — `rows scanned` giảm ≥ 10×, `result hash` không đổi, số file giảm | +5 |
| **Bài B** — `make crash-test` đạt, báo cáo giải thích được at-most-once / at-least-once / idempotent write | +5 |

---

## Trừ điểm

| | |
|---|---|
| Sửa `expected/`, `tools/verify.py`, `tools/explain.py` hoặc `seed/generate.py` để đạt tiêu chí | **0 điểm toàn bài** |
| Xoá bớt dữ liệu nguồn cho số hàng khớp | **0 điểm toàn bài** |
| Nộp kèm `.venv/`, `warehouse.duckdb`, `data/` (không chạy `make clean`) | −3 |
| `make verify` không chạy được trên repo nộp (thiếu file, lỗi import) | −10 |

> Bạn **được phép** sửa mọi thứ trong `dbt/`, `ingest/`, `queries/`,
> `tools/compact.py`, `dags/`. Bạn **không được** sửa `expected/`,
> `seed/generate.py`, `tools/verify.py`, `tools/explain.py`, `tools/common.py`.

---

## Bảng tự chấm nhanh

Điền trước khi nộp:

| | Của tôi | Kỳ vọng | ✓/✗ |
|---|---|---|---|
| `gold_training_set` — số hàng | 12.480 | 12.480 | ✓ |
| `gold_training_set` — ổn định 3 lượt | ✓, checksum `8dd7c98653` cả 3 lượt | ✓ | ✓ |
| `gold_feature_daily` — số hàng | 9.100 | 9.100 | ✓ |
| `gold_feature_daily` — ổn định 3 lượt | ✓, checksum `3db448685c` cả 3 lượt | ✓ | ✓ |
| `gold_doc_chunks` — số hàng | 31.200 | 31.200 | ✓ |
| `quarantine_tickets` — số hàng | 312 | 312 | ✓ |
| `silver_tickets` — số ticket | 12.480 | 12.480 | ✓ |
| `dbt test` | 11/11 pass | pass, > 9 test | ✓ |
| P99 độ trễ đo được | 2,73 ngày | (ghi số) | ✓ |
| **Tổng verify** | 4/4 tiêu chí | 4/4 tiêu chí | ✓ |
| **Thưởng A — dashboard** | rows scanned `5.000.000 → 136.934` (36,5×), files `5.000 → 14`, hash không đổi | giảm ≥ 10×, hash không đổi, files giảm | ✓ |
| **Thưởng B — crash-test** | đạt; 20.000 hàng / 20.000 event_id, không mất, không trùng, C == A | `make crash-test` đạt | ✓ |
