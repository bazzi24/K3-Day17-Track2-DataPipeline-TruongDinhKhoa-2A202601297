-- ---------------------------------------------------------------------------
-- quarantine_tickets — nơi tiếp nhận bản ghi CDC không thoả data contract.
-- ---------------------------------------------------------------------------
-- NHIỆM VỤ 3 — phần 3/3.  Model đã được nối sẵn, bạn chỉ điền mệnh đề WHERE.
--
-- Grain: 1 hàng / 1 BẢN GHI CDC bị loại — không phải 1 hàng / 1 ticket.
--        Một ticket có nhiều bản ghi CDC, thường chỉ một bản ghi bị hỏng.
-- Số hàng kỳ vọng: xem expected/quarantine_tickets.count
--
-- Điều kiện lọc phải dùng ĐÚNG macro mà silver_tickets dùng, để hai model
-- không thể lệch nhau: bản ghi nào bị loại khỏi Silver thì xuất hiện ở đây,
-- không thừa không thiếu. Cụ thể: lọc những hàng mà macro normalize_priority
-- trả về NULL.
--
-- Vì sao tách riêng thay vì để pipeline dừng: vài trăm bản ghi hỏng không có
-- quyền chặn hơn 130.000 event và 31.200 chunk hoàn toàn bình thường đến tay
-- người dùng. Pipeline chạy tiếp, bảng này là hàng đợi cho người trực xử lý.
-- ---------------------------------------------------------------------------

{{ config(materialized = 'table') }}

select
    ticket_id,
    cdc_seq,
    op,
    event_time,
    _ingested_at,
    priority_raw,
    {{ priority_reject_reason('priority_raw') }}             as reject_reason,
    customer_id,
    customer_name,
    category,
    status
from {{ source('bronze', 'bronze_tickets_cdc') }}

-- TODO(nhiệm vụ 3): thay `false` bằng điều kiện "priority không chuẩn hoá
-- được". Khi còn `false`, bảng rỗng và make verify báo 0 / <số kỳ vọng>.
where {{ normalize_priority('priority_raw') }} is null
