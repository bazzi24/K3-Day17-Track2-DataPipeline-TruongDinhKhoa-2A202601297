"""DAG Airflow đang chạy pipeline này trên production.

⚠️  KHÔNG cần cài Airflow. File này KHÔNG được import lúc chạy lab —
    `make pipeline` gọi thẳng tools/run_pipeline.py. Ở đây nó đóng vai
    "hiện trường vụ án": phiếu #1041 nói người trực đã bấm **Clear Task**
    trong Airflow, và hai tham số của DAG quyết định điều gì xảy ra sau đó.

    `make verify` đọc file này bằng AST (không import) và kiểm tra hai
    tham số ở phần TODO bên dưới.
"""

from __future__ import annotations

import datetime as dt

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": dt.timedelta(minutes=5),
}

with DAG(
    dag_id="ai_training_pipeline",
    description="Bronze -> Silver -> Gold cho nền tảng AI hỗ trợ khách hàng",
    start_date=dt.datetime(2026, 8, 3),
    schedule="0 2 * * *",
    default_args=DEFAULT_ARGS,
    tags=["ai-support", "daily"],
    # ------------------------------------------------------------------
    # TODO (nhiệm vụ 1): hai tham số dưới đây quyết định chuyện gì xảy ra
    # khi ai đó bấm Clear Task, và khi DAG bị dồn nhiều lần chạy cùng lúc.
    # Đọc lại triệu chứng ở phiếu #1041 rồi đặt lại cho đúng.
    catchup=False,
    max_active_runs=1,
    # ------------------------------------------------------------------
) as dag:

    load_bronze = BashOperator(
        task_id="load_bronze",
        bash_command=(
            "python ingest/load_bronze.py --run-date {{ ds }}"
        ),
    )

    build_silver = BashOperator(
        task_id="build_silver",
        bash_command=(
            "dbt run --select silver --vars '{\"run_date\": \"{{ ds }}\"}'"
        ),
    )

    build_gold = BashOperator(
        task_id="build_gold",
        bash_command=(
            "dbt run --select gold --vars '{\"run_date\": \"{{ ds }}\"}'"
        ),
    )

    test_data = BashOperator(
        task_id="test_data",
        bash_command="dbt test",
    )

    load_bronze >> build_silver >> build_gold >> test_data
