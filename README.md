# databricks-github-action

A reference project demonstrating how to deploy **Databricks Asset Bundles (DAB)** to a Databricks workspace using **GitHub Actions**. It provisions Unity Catalog resources (catalog, schema, volumes), a DLT pipeline (bronze + silver layers), and a scheduled job — all through a single automated CI/CD workflow.

---

## Overview

```
┌─────────────────────────────────────────────────┐
│                  GitHub Actions                  │
│  push to main → validate → deploy → run pipeline │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│           Databricks Asset Bundle (DAB)          │
│                                                  │
│  ┌─────────────┐   ┌───────────────────────────┐ │
│  │   Resources │   │         src/              │ │
│  │  catalog    │   │  bronze_table.py  (DLT)   │ │
│  │  schema     │   │  silver_tables.sql (DLT)  │ │
│  │  volumes    │   │  hello.py         (Job)   │ │
│  │  pipeline   │   └───────────────────────────┘ │
│  │  job        │                                  │
│  └─────────────┘                                  │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│        Unity Catalog (dev_catalog.bronze)        │
│                                                  │
│  raw_events table  (bronze, DLT)                 │
│  raw_customers table (silver, DLT)               │
│  contracts_volume  (managed)                     │
│  landing volume    (managed)                     │
└─────────────────────────────────────────────────┘
```

---

## Project Structure

```
databricks-github-action/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD pipeline
├── resources/
│   ├── catalog.yml             # Unity Catalog definition
│   ├── schemas.yml             # Bronze schema
│   ├── volume.yml              # Managed volumes (contracts + landing)
│   ├── pipelines.yml           # DLT pipeline (bronze ingestion)
│   └── job.yml                 # Scheduled Databricks Job
├── src/
│   ├── bronze_table.py         # DLT: raw_events table (Python)
│   ├── silver_tables.sql       # DLT: raw_customers table (SQL)
│   └── hello.py                # Simple notebook task for the job
├── databricks.yml              # Root bundle config + variables + targets
├── databricks.md               # DAB cheat sheet / reference docs
└── pyproject.toml              # Python project config (uv / pip)
```

---

## Prerequisites

| Tool | Purpose |
|---|---|
| [Databricks CLI v0.200+](https://docs.databricks.com/dev-tools/cli/index.html) | Bundle deploy & run |
| A Databricks workspace with Unity Catalog enabled | Target environment |
| A service principal with sufficient permissions | CI/CD identity (`run_as`) |
| GitHub repository secrets configured | Auth for GitHub Actions |

---

## GitHub Actions Workflow

The [deploy.yml](.github/workflows/deploy.yml) workflow triggers on every push to `main` and runs three steps:

```yaml
- run: databricks bundle validate   # Lint & type-check the bundle
- run: databricks bundle deploy     # Deploy all resources to dev
- run: databricks bundle run bronze_pipeline  # Trigger the DLT pipeline
```

### Required Secrets

Add these in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `DATABRICKS_HOST` | Your workspace URL, e.g. `https://adb-xxxx.azuredatabricks.net` |
| `DATABRICKS_TOKEN` | A personal access token **or** use OIDC for keyless auth |

---

## Local Development

### 1. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or pip
pip install -e .
```

### 2. Authenticate with Databricks

```bash
databricks configure
# or set env vars:
export DATABRICKS_HOST=https://adb-xxxx.azuredatabricks.net
export DATABRICKS_TOKEN=dapiXXXXXXXXXXX
```

### 3. Validate the bundle

```bash
databricks bundle validate
```

### 4. Deploy to dev

```bash
databricks bundle deploy --target dev
```

### 5. Run the pipeline

```bash
databricks bundle run bronze_pipeline
```

---

## Bundle Variables

Defined in [`databricks.yml`](databricks.yml) and resolved per target:

| Variable | Dev Default | Description |
|---|---|---|
| `catalog_name` | `dev_catalog` | Unity Catalog name |
| `schema_name` | `bronze` | Schema within the catalog |
| `contracts_volume_name` | `contracts_volume` | Managed volume for contracts data |
| `landing_volume_name` | `landing` | Managed volume for raw landing data |

Override at deploy time:

```bash
databricks bundle deploy --target dev \
  --var catalog_name=my_catalog \
  --var schema_name=my_schema
```

---

## Resources

### DLT Pipeline — `bronze_ingestion_pipeline`

Defined in [`resources/pipelines.yml`](resources/pipelines.yml). Runs **serverless**, in **triggered** (non-continuous) mode.

| Notebook | Layer | Table | Description |
|---|---|---|---|
| `src/bronze_table.py` | Bronze | `raw_events` | Raw event data ingested from JSON volume |
| `src/silver_tables.sql` | Silver | `raw_customers` | Raw customer data ingested from JSON volume |

### Job — `Hello Job`

Defined in [`resources/job.yml`](resources/job.yml). Runs `src/hello.py` on a **cron schedule** (every 2 hours, `Asia/Kolkata` timezone). Paused by default.

### Unity Catalog Resources

| Resource | Type | Config file |
|---|---|---|
| `dev_catalog` | Catalog | `resources/catalog.yml` |
| `bronze` schema | Schema | `resources/schemas.yml` |
| `contracts_volume` | Managed Volume | `resources/volume.yml` |
| `landing` | Managed Volume | `resources/volume.yml` |

---

## Data Flow

```
JSON files in /Volumes/dev_catalog/bronze/landing/
        │
        ├──▶ bronze_table.py  ──▶  raw_events    (DLT Bronze)
        │
        └──▶ silver_tables.sql ──▶ raw_customers  (DLT Silver)
```

> **Note:** Both tables are currently initialised with **schema-only** (no rows loaded). To activate ingestion, uncomment the `spark.read` block in `bronze_table.py` and remove the `WHERE 1=0` clause in `silver_tables.sql`.

---

## Targets

Only `dev` is currently configured. To add `prod`, extend `databricks.yml`:

```yaml
targets:
  dev:
    default: true
    variables:
      catalog_name: dev_catalog

  prod:
    variables:
      catalog_name: prod_catalog
    run_as:
      service_principal_name: <prod-sp-id>
```

Deploy to prod:

```bash
databricks bundle deploy --target prod
```

---

## References

- [Databricks Asset Bundles docs](https://docs.databricks.com/dev-tools/bundles/index.html)
- [databricks/setup-cli GitHub Action](https://github.com/databricks/setup-cli)
- [Delta Live Tables](https://docs.databricks.com/delta-live-tables/index.html)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [`databricks.md`](databricks.md) — local DAB cheat sheet included in this repo

---

## License

[MIT](LICENSE)
