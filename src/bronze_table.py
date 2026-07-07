import dlt
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

events_schema = StructType([
    StructField("event_id", StringType(), nullable=False),
    StructField("event_time", TimestampType(), nullable=True),
    StructField("payload", StringType(), nullable=True),
])

@dlt.table(
    name="raw_events",
    comment="Raw event data"
)
def raw_events():
    return (
        spark.read
        .schema(events_schema)
        .format("json")
        .load("/Volumes/dev_catalog/bronze/landing/events")
    )