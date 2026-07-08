# Databricks notebook source

import dlt
from pyspark.sql.types import (
    StructType, StructField,
    StringType, TimestampType,
)

# COMMAND ----------
# BRONZE LAYER — Raw ingestion, schema-enforced, no cleaning

# COMMAND ----------

clickstream_schema = StructType([
    StructField("event_id",   StringType(),    nullable=False),
    StructField("user_id",    StringType(),    nullable=True),
    StructField("session_id", StringType(),    nullable=True),
    StructField("event_type", StringType(),    nullable=True),
    StructField("page_url",   StringType(),    nullable=True),
    StructField("referrer",   StringType(),    nullable=True),
    StructField("event_time", TimestampType(), nullable=True),
])

customers_schema = StructType([
    StructField("customer_id", StringType(),    nullable=False),
    StructField("name",        StringType(),    nullable=True),
    StructField("email",       StringType(),    nullable=True),
    StructField("country",     StringType(),    nullable=True),
    StructField("created_at",  TimestampType(), nullable=True),
])

# COMMAND ----------

@dlt.table(
    name="raw_clickstream",
    comment="Raw clickstream events — append-only, schema-enforced ingestion from landing volume"
)
def raw_clickstream():
    return (
        spark.read
        .schema(clickstream_schema)
        .format("json")
        .load("/Volumes/dev_catalog/bronze/landing/clickstream")
    )

# COMMAND ----------

@dlt.table(
    name="raw_customers",
    comment="Raw customer records — append-only, schema-enforced ingestion from landing volume"
)
def raw_customers():
    return (
        spark.read
        .schema(customers_schema)
        .format("json")
        .load("/Volumes/dev_catalog/bronze/landing/customers")
    )