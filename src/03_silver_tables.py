# Databricks notebook source

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------
# SILVER LAYER — Cleaned, deduplicated, and sessionised data

# COMMAND ----------

@dlt.expect_or_drop("valid_event_id",  "event_id IS NOT NULL")
@dlt.expect_or_drop("valid_user_id",   "user_id IS NOT NULL")
@dlt.expect_or_drop("valid_event_time","event_time IS NOT NULL")
@dlt.table(
    name="clean_clickstream",
    schema="silver",
    catalog="dev_catalog",
    comment="Deduplicated, validated clickstream events with a processed_at audit column"
)
def clean_clickstream():
    # Deduplicate on event_id — keep the first occurrence by event_time
    window = Window.partitionBy("event_id").orderBy("event_time")
    return (
        dlt.read("raw_clickstream")
        .withColumn("_row_num", F.row_number().over(window))
        .filter(F.col("_row_num") == 1)
        .drop("_row_num")
        .withColumn("processed_at", F.current_timestamp())
    )

# COMMAND ----------

@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
@dlt.expect_or_drop("valid_email",       "email IS NOT NULL AND email LIKE '%@%'")
@dlt.table(
    name="clean_customers",
    schema="silver",
    catalog="dev_catalog",
    comment="Validated customer records with normalised email addresses"
)
def clean_customers():
    return (
        dlt.read("raw_customers")
        .filter(F.col("customer_id").isNotNull())
        .withColumn("email", F.lower(F.trim(F.col("email"))))
        .withColumn("processed_at", F.current_timestamp())
    )

# COMMAND ----------

@dlt.table(
    name="sessions",
    schema="silver",
    catalog="dev_catalog",
    comment="User sessions derived by 30-minute inactivity gap windowing on clean_clickstream"
)
def sessions():
    # Sessionise: flag a new session when the gap from the previous event
    # for the same user exceeds 30 minutes (1800 seconds).
    user_time_window = Window.partitionBy("user_id").orderBy("event_time")

    with_lag = (
        dlt.read("clean_clickstream")
        .withColumn(
            "prev_event_time",
            F.lag("event_time").over(user_time_window)
        )
        .withColumn(
            "gap_seconds",
            F.coalesce(
                (F.unix_timestamp("event_time") - F.unix_timestamp("prev_event_time")),
                F.lit(0)
            )
        )
        .withColumn(
            "is_new_session",
            F.when(F.col("gap_seconds") > 1800, 1).otherwise(0)
        )
        # Assign a monotonically increasing session boundary marker per user
        .withColumn(
            "session_boundary",
            F.sum("is_new_session").over(
                user_time_window.rowsBetween(Window.unboundedPreceding, 0)
            )
        )
        # Build a stable session key: user_id + boundary index
        .withColumn(
            "session_key",
            F.concat_ws("_", F.col("user_id"), F.col("session_boundary").cast("string"))
        )
    )

    return (
        with_lag
        .groupBy("session_key", "user_id", "session_id")
        .agg(
            F.min("event_time").alias("session_start"),
            F.max("event_time").alias("session_end"),
            F.count("event_id").alias("event_count"),
            F.round(
                (F.unix_timestamp(F.max("event_time")) - F.unix_timestamp(F.min("event_time"))),
                1
            ).alias("session_duration_seconds"),
        )
        .withColumn("processed_at", F.current_timestamp())
    )
