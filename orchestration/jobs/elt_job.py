from dagster import define_asset_job


elt_job = define_asset_job(
    name="elt_job",
)