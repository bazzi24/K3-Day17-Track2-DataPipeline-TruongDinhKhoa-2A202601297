#!/usr/bin/env python3
"""Tái cấu trúc dataset Parquet của dashboard — NHIỆM VỤ 4.  CHƯA CÓ LOGIC.

Hiện trạng: `data/gold_events/` gồm 5.000 file, mỗi file vài chục KB, không
partition, thứ tự hàng ngẫu nhiên.

Yêu cầu: đọc toàn bộ dataset cũ, ghi ra dataset mới có layout hợp lý hơn, sau đó cập
nhật `queries/dashboard.sql` để trỏ vào dataset mới.

    python tools/compact.py       # ghi dataset mới
    python tools/explain.py       # đo lại và so với baseline

KHUNG THỰC HIỆN

    COPY (
        SELECT *
        FROM   read_parquet('data/gold_events/*.parquet')
        ORDER  BY <cột A>, <cột B>
    ) TO 'data/gold_events_v2' (
        FORMAT          parquet,
        PARTITION_BY    (<cột partition>),
        OVERWRITE_OR_IGNORE,
        ROW_GROUP_SIZE  <?>
    )

Ba quyết định, mỗi quyết định cần một lý do viết được ra giấy:

  <cột partition>   Engine chỉ bỏ qua được file mà nó biết là vô ích TRƯỚC khi
                    mở file. Thông tin đó đến từ đường dẫn. Vậy cột nào của
                    truy vấn dashboard nên xuất hiện trong tên thư mục? Cột đó
                    có bao nhiêu giá trị phân biệt — tức bao nhiêu thư mục?
                    Partition theo cột có 650 giá trị thì hệ quả là gì?

  <cột A>, <cột B>  Thứ tự hàng trong file quyết định thống kê min/max của mỗi
                    row group có ích hay vô dụng. Sắp thế nào để các hàng cùng
                    một khách hàng nằm liền nhau?

  ROW_GROUP_SIZE    Mặc định 122.880 hàng. Một ngày có khoảng bao nhiêu hàng?
                    Nếu cả ngày gói gọn trong MỘT row group thì min/max của
                    row group đó phủ những gì, và còn tác dụng lọc không?

Sau khi chạy xong, kiểm tra lại bằng `python tools/explain.py`: `rows scanned`
phải giảm, `files` phải giảm, và `result hash` phải GIỮ NGUYÊN.
"""

from __future__ import annotations

import pathlib
import shutil
import sys

import duckdb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from tools.common import DATA  # noqa: E402

SRC = DATA / "gold_events"
DST = DATA / "gold_events_v2"


def main() -> int:
    con = duckdb.connect()

    n_src = len(list(SRC.glob("*.parquet")))
    print(f"  nguồn : {SRC}  ({n_src:,} file)")

    if n_src == 0:
        raise SystemExit("  ✗ không thấy file nguồn; chạy `make seed-extra` trước")

    shutil.rmtree(DST, ignore_errors=True)

    src_pattern = str(SRC / "*.parquet")
    dst = str(DST)
    n_rows_src = con.execute(
        "select count(*) from read_parquet(?)",
        [src_pattern],
    ).fetchone()[0]

    con.execute(f"""
        copy (
            select
                *,
                event_time::date as event_date
            from read_parquet('{src_pattern}')
            order by event_date, customer_name, event_time
        ) to '{dst}' (
            format parquet,
            partition_by (event_date),
            overwrite_or_ignore,
            row_group_size 2048
        )
    """)

    n_rows_dst = con.execute(
        "select count(*) from read_parquet(?, hive_partitioning = true)",
        [str(DST / "**" / "*.parquet")],
    ).fetchone()[0]
    assert n_rows_src == n_rows_dst, (n_rows_src, n_rows_dst)

    n_dst = len(list(DST.glob("**/*.parquet")))
    print(f"  đích  : {DST}  ({n_dst:,} file)")
    print(f"  số row: {n_rows_src:,} -> {n_rows_dst:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
