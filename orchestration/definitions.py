from pathlib import Path

from dagster import Definitions
from dagster_dbt import DbtCliResource

from orchestration.assets.ingestion import (
    raw_customers,
    raw_orders,
    raw_products,
)
from orchestration.assets.dbt_assets import (
    DBT_PROJECT_DIR,
    dbt_models,
)
from orchestration.jobs.elt_job import elt_job


defs = Definitions(
    assets=[
        raw_orders,
        raw_customers,
        raw_products,
        dbt_models,
    ],
    jobs=[
        elt_job,
    ],
    resources={
        "dbt": DbtCliResource(
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROJECT_DIR,
            target="dev",
        ),
    },
)