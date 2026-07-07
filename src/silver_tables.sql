-- Databricks notebook source
CREATE OR REFRESH LIVE TABLE raw_customers (
  customer_id STRING NOT NULL,
  name STRING,
  email STRING,
  created_at TIMESTAMP
)
COMMENT "Raw customer data"
AS SELECT
  customer_id,
  name,
  email,
  CAST(created_at AS TIMESTAMP) AS created_at
FROM json.`/Volumes/dev_catalog/bronze/landing/customers`