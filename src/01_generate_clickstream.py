# Databricks notebook source

# COMMAND ----------
# Synthetic Clickstream Data Generator
# Writes JSON files to the landing volume for downstream DLT ingestion.

import json
import random
import uuid
from datetime import datetime, timedelta, timezone

# COMMAND ----------

LANDING_BASE = "/Volumes/dev_catalog/bronze/landing"
NUM_USERS = 50
NUM_EVENTS = 1_000
NUM_CUSTOMERS = 100

EVENT_TYPES = ["page_view", "click", "add_to_cart", "purchase"]
EVENT_WEIGHTS = [0.55, 0.25, 0.12, 0.08]  # realistic funnel distribution

PAGES = [
    "/", "/products", "/products/42", "/products/17", "/products/99",
    "/cart", "/checkout", "/order-confirmation", "/about", "/contact",
    "/blog", "/blog/summer-sale", "/account", "/search",
]

REFERRERS = [
    "google.com", "facebook.com", "instagram.com", "twitter.com",
    "direct", "newsletter", "bing.com", "reddit.com",
]

COUNTRIES = ["IN", "US", "GB", "DE", "AU", "SG", "CA", "FR"]

FIRST_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eva", "Frank", "Grace", "Hiro"]
LAST_NAMES  = ["Smith", "Kumar", "Zhang", "Müller", "Okafor", "Tanaka", "Santos", "Lee"]

# COMMAND ----------

def random_timestamp(days_back: int = 7) -> str:
    now = datetime.now(timezone.utc)
    delta = timedelta(
        seconds=random.randint(0, days_back * 24 * 3600)
    )
    ts = now - delta
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_users(n: int) -> list[str]:
    return [str(uuid.uuid4()) for _ in range(n)]


def generate_events(user_ids: list[str], n: int) -> list[dict]:
    events = []
    for _ in range(n):
        user_id = random.choice(user_ids)
        session_id = str(uuid.uuid4())
        # Each user can have a short burst of events in the same session
        num_session_events = random.randint(1, 8)
        base_time_str = random_timestamp()
        base_time = datetime.strptime(base_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

        for i in range(num_session_events):
            event_time = base_time + timedelta(seconds=random.randint(5, 300) * i)
            events.append({
                "event_id":   str(uuid.uuid4()),
                "user_id":    user_id,
                "session_id": session_id,
                "event_type": random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0],
                "page_url":   random.choice(PAGES),
                "referrer":   random.choice(REFERRERS),
                "event_time": event_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            })
    # Trim to exactly n events
    return events[:n]


def generate_customers(user_ids: list[str], n: int) -> list[dict]:
    sampled = random.sample(user_ids, min(n, len(user_ids)))
    customers = []
    for uid in sampled:
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        customers.append({
            "customer_id": uid,
            "name":        f"{first} {last}",
            "email":       f"{first.lower()}.{last.lower()}{random.randint(1,999)}@example.com",
            "country":     random.choice(COUNTRIES),
            "created_at":  random_timestamp(days_back=365),
        })
    return customers

# COMMAND ----------

user_ids   = generate_users(NUM_USERS)
events     = generate_events(user_ids, NUM_EVENTS)
customers  = generate_customers(user_ids, NUM_CUSTOMERS)

timestamp  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

events_path    = f"{LANDING_BASE}/clickstream/events_{timestamp}.json"
customers_path = f"{LANDING_BASE}/customers/customers_{timestamp}.json"

# COMMAND ----------
# Clear existing files from the landing subdirectories before writing.
# This prevents data from accumulating across CI runs — without this,
# every push would add a new file and bronze tables would grow unbounded
# since spark.read() reads ALL files in the directory on each pipeline run.

for folder in [f"{LANDING_BASE}/clickstream", f"{LANDING_BASE}/customers"]:
    try:
        dbutils.fs.rm(folder, recurse=True)
        print(f"🧹 Cleared {folder}")
    except Exception:
        pass  # Folder may not exist on first run — that's fine

# COMMAND ----------

# Write clickstream events — one JSON object per line (newline-delimited JSON)
events_ndjson    = "\n".join(json.dumps(e) for e in events)
customers_ndjson = "\n".join(json.dumps(c) for c in customers)

dbutils.fs.put(events_path,    events_ndjson,    overwrite=True)
dbutils.fs.put(customers_path, customers_ndjson, overwrite=True)

print(f"✅ Wrote {len(events)} events    → {events_path}")
print(f"✅ Wrote {len(customers)} customers → {customers_path}")
