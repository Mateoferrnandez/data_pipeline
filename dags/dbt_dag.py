import os
from datetime import datetime

from cosmos import DbtDag , ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import SnowflakeEncryptedPrivateKeyFilePemProfileMapping

profile_config = ProfileConfig(
    profile_name="default",
    target_name="dev",
    profile_mapping=SnowflakeEncryptedPrivateKeyFilePemProfileMapping(
      conn_id="snowflake_conn",
      profile_args={
        "database": "dbt_db",
        "schema": "dbt_schema",
        "warehouse": "dbt_wh",
        "role": "dbt_role",
        "private_key_path": f"{os.environ['AIRFLOW_HOME']}/dags/dbt/data_pipeline/rsa_key.p8",}
    )
)
    


dbt_snowflake_dag = DbtDag(
    project_config=ProjectConfig(f"{os.environ['AIRFLOW_HOME']}/dags/dbt/data_pipeline"),
    operator_args={"install_deps": True},
    profile_config=profile_config,
    execution_config=ExecutionConfig(dbt_executable_path=f"{os.environ['AIRFLOW_HOME']}/dbt_venv/bin/dbt"),
    schedule="@daily",
    start_date=datetime(2026, 9, 28),
    catchup=False,
    dag_id="dbt_dag",
)
    