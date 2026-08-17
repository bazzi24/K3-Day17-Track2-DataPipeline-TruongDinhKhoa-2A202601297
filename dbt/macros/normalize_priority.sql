{#
    ==========================================================================
    NHIỆM VỤ 3 — phần 1/3.  Đây là nơi bạn sửa.
    ==========================================================================

    Macro trong dbt = một đoạn SQL đặt tên, dùng lại được ở nhiều model.
    Gọi nó bằng {{ normalize_priority('priority_raw') }} và dbt sẽ chèn nội
    dung bên dưới vào đúng chỗ đó.

    Macro này đang được dùng ở HAI nơi:
        models/silver/silver_tickets.sql      -> để lấy giá trị đã chuẩn hoá
        models/silver/quarantine_tickets.sql  -> để tìm bản ghi KHÔNG chuẩn
                                                 hoá được
    Nhờ vậy hai model không thể lệch nhau: sửa ở đây là cả hai cùng đổi.

    --------------------------------------------------------------------------
    Cột `priority` phải là số nguyên 1..4. Hãy xem nguồn đang gửi gì:

        select priority_raw, count(*) from bronze_tickets_cdc group by 1 order by 2 desc;

    Bạn sẽ thấy BA nhóm giá trị, và ba nhóm này KHÔNG xử lý giống nhau:

      Nhóm 1   '1' '2' '3' '4'
               Đúng contract cũ.                            -> GIỮ NGUYÊN

      Nhóm 2   'urgent' 'high' 'medium' 'low'
               Từ 2026-08-10 team backend đổi cách ghi: dùng nhãn chữ thay
               cho số. Ý nghĩa KHÔNG đổi, chỉ đổi cách biểu diễn.
               Theo tài liệu API: urgent=1, high=2, medium=3, low=4.
                                                            -> QUY VỀ SỐ

      Nhóm 3   'P1' 'unknown' '0' '5' '-1' '' NULL
               Dữ liệu hỏng thật.                           -> TRẢ VỀ NULL
               (NULL ở đây là tín hiệu "không hợp lệ" — quarantine_tickets
                dùng chính tín hiệu đó để nhặt bản ghi lỗi ra.)

    ⚠️ Lỗi hay gặp nhất: xử lý nhóm 2 như nhóm 3. Nếu bạn để nhãn chữ rơi
       vào NULL thì quarantine sẽ có hàng nghìn hàng thay vì vài trăm, và
       bạn vừa vứt đi một nửa dữ liệu tốt chỉ vì nguồn đổi format.

    ⚠️ Chú ý `try_cast` hiện tại sai theo HAI hướng ngược nhau: nó biến nhãn
       chữ thành NULL, ĐỒNG THỜI lại chấp nhận '0', '5', '-1' vì chúng đúng
       là số — dù contract nói chỉ 1..4.
    ==========================================================================
#}

{% macro normalize_priority(col) %}
    case
        when try_cast({{ col }} as integer) between 1 and 4
            then try_cast({{ col }} as integer)
        when lower(trim({{ col }})) = 'urgent' then 1
        when lower(trim({{ col }})) = 'high' then 2
        when lower(trim({{ col }})) = 'medium' then 3
        when lower(trim({{ col }})) = 'low' then 4
        else null
    end
{% endmacro %}


{#
    Lý do bị loại — để người trực đọc log là hiểu ngay phải làm gì.
    Bắt đầu bằng một câu chung cũng được; phân biệt được vài loại lỗi thì tốt
    hơn (rỗng / NULL / là số nhưng ngoài khoảng / là chuỗi lạ).
#}
{% macro priority_reject_reason(col) %}
    case
        when {{ col }} is null then 'priority bị null'
        when trim({{ col }}) = '' then 'priority rỗng'
        when try_cast({{ col }} as integer) is not null
            then 'priority dạng số nhưng ngoài khoảng 1..4'
        else 'priority là chuỗi không được hỗ trợ'
    end
{% endmacro %}
