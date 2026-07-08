# Databricks notebook source

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------
# GOLD LAYER — Aggregated analytics tables
# All tables read from silver via dlt.read() and are materialised as DLT tables.

# COMMAND ----------

@dlt.table(
    name="daily_traffic_metrics",
    schema="gold",
    comment="Daily session and traffic summary — sessions/day, unique users, avg duration, total events"
)
def daily_traffic_metrics():
    return (
        dlt.read("sessions")
        .withColumn("date", F.to_date("session_start"))
        .groupBy("date")
        .agg(
            F.count("session_id").alias("total_sessions"),
            F.countDistinct("user_id").alias("unique_users"),
            F.round(F.avg("session_duration_seconds"), 1).alias("avg_session_duration_seconds"),
            F.sum("event_count").alias("total_events"),
        )
        .orderBy("date")
    )

# COMMAND ----------

@dlt.table(
    name="funnel_conversion",
    schema="gold",
    comment="Event-type funnel: session counts per stage and conversion rate relative to page_view"
)
def funnel_conversion():
    # Count distinct sessions that included each event type
    clickstream = dlt.read("clean_clickstream")

    stage_counts = (
        clickstream
        .groupBy("event_type")
        .agg(F.countDistinct("session_id").alias("session_count"))
    )

    # Grab page_view count to compute relative conversion rates
    page_view_count = (
        clickstream
        .filter(F.col("event_type") == "page_view")
        .agg(F.countDistinct("session_id").alias("cnt"))
        .collect()[0]["cnt"]
    )

    return (
        stage_counts
        .withColumn(
            "conversion_rate",
            F.when(
                F.lit(page_view_count) > 0,
                F.round(F.col("session_count") / F.lit(page_view_count), 4)
            ).otherwise(F.lit(None))
        )
        .orderBy(F.col("session_count").desc())
    )

# COMMAND ----------

@dlt.table(
    name="top_pages",
    schema="gold",
    comment="Most-visited pages ranked by view count with unique user reach"
)
def top_pages():
    return (
        dlt.read("clean_clickstream")
        .filter(F.col("event_type") == "page_view")
        .groupBy("page_url")
        .agg(
            F.count("event_id").alias("view_count"),
            F.countDistinct("user_id").alias("unique_users"),
        )
        .withColumn("rank", F.rank().over(
            Window.orderBy(F.col("view_count").desc())
        ))
        .orderBy("rank")
    )
