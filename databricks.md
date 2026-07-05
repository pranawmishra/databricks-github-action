# Databricks Asset Bundles (`databricks.yml`) Cheat Sheet

---

# 1. `bundle`

### Purpose

Defines the name of your Databricks Asset Bundle.

### Example

```yaml
bundle:
  name: dab-demo
```

### Why use it?

* Identifies your project.
* Used internally by Databricks during deployment.

---

# 2. `include`

### Purpose

Includes other YAML files into the bundle.

### Example

```yaml
include:
  - resources/*.yml
```

### Why use it?

Instead of putting everything into one file, you can organize your project.

Example:

```
resources/
    jobs.yml
    pipelines.yml
    dashboards.yml
```

---

# 3. `targets`

### Purpose

Defines deployment environments.

### Example

```yaml
targets:

  dev:
    default: true

  test:

  prod:
```

### Why use it?

Deploy the same project to different environments.

Example:

```
Development
Testing
Production
```

Deploy using:

```bash
databricks bundle deploy --target dev
```

or

```bash
databricks bundle deploy --target prod
```

---

# 4. `workspace`

### Purpose

Specifies which Databricks workspace to deploy to.

### Example

```yaml
targets:

  dev:
    workspace:
      host: https://adb-dev.azuredatabricks.net

  prod:
    workspace:
      host: https://adb-prod.azuredatabricks.net
```

### Why use it?

Useful when different environments have different Databricks workspaces.

> **Note:** In GitHub Actions, authentication usually comes from the environment variables `DATABRICKS_HOST` and `DATABRICKS_TOKEN`, so you often don't need to specify `workspace.host` in `databricks.yml`.

---

# 5. `variables`

### Purpose

Create reusable variables instead of hardcoding values.

### Example

```yaml
variables:

  cluster_id:
    description: Existing Cluster

  catalog_name:
    description: Unity Catalog
```

Use them:

```yaml
existing_cluster_id: ${var.cluster_id}
```

Deploy:

```bash
databricks bundle deploy \
    --var cluster_id=0518-123abc
```

### Why use it?

Instead of:

```yaml
existing_cluster_id: 0518-123abc
```

You write:

```yaml
existing_cluster_id: ${var.cluster_id}
```

Making your project reusable across environments.

---

# 6. Variable Defaults

### Purpose

Provide default values for variables.

### Example

```yaml
variables:

  catalog:
    default: dev_catalog
```

### Why use it?

If no value is provided during deployment,

```
catalog = dev_catalog
```

---

# 7. `run_as`

### Purpose

Specify which user or service principal executes the deployed resources.

### Example

User:

```yaml
run_as:
  user_name: abc@company.com
```

Service Principal:

```yaml
run_as:
  service_principal_name: xxxxxxxxx
```

### Why use it?

Production jobs usually run under service principals instead of personal accounts.

---

# 8. `sync`

### Purpose

Control which files get uploaded to Databricks.

### Example

```yaml
sync:

  include:
    - src/**

  exclude:
    - tests/**
    - docs/**
```

### Why use it?

Suppose your repository looks like:

```
README.md
docs/
tests/
src/
scripts/
```

Only upload:

```
src/
```

Ignore:

```
docs/
tests/
```

---

# 9. `artifacts`

### Purpose

Automatically build Python packages before deployment.

### Example

```yaml
artifacts:

  default:
    type: whl

    build: |
      python -m pip install -U build
      python -m build
```

### Why use it?

Deployment flow:

```
Build Wheel
      ↓
Upload Wheel
      ↓
Install Wheel
      ↓
Run Job
```

Very common for production projects.

---

# 10. `permissions`

### Purpose

Assign permissions during deployment.

### Example

```yaml
permissions:

  - level: CAN_MANAGE
    user_name: abc@company.com
```

### Why use it?

Avoid manually configuring permissions in the Databricks UI.

---

# 11. Presets

### Purpose

Apply common settings to multiple resources.

### Why use it?

Instead of manually naming resources:

```
Dev Job
Dev Pipeline
Dev Dashboard
```

You can automatically apply prefixes or other common configurations.

---

# 12. Git Information

### Purpose

Associate deployments with Git commits and repository metadata.

### Why use it?

Useful for:

* Deployment tracking
* Rollbacks
* Auditing

---

# 13. Scripts / Hooks

### Purpose

Run custom commands before or after deployment.

### Example Workflow

```
Run Unit Tests
        ↓
Validate Bundle
        ↓
Deploy Bundle
        ↓
Send Slack Notification
```

Useful for CI/CD pipelines.

---

# Typical Production `databricks.yml`

```yaml
bundle:
  name: customer-etl

include:
  - resources/*.yml

variables:
  cluster_id:
    description: Existing Cluster

targets:

  dev:
    default: true

  prod:

artifacts:

  default:
    type: whl
    build: |
      python -m build

sync:
  include:
    - src/**
  exclude:
    - tests/**
```

---

# Summary Table

| Feature               | Purpose                                  | Common Use                       |
| --------------------- | ---------------------------------------- | -------------------------------- |
| **bundle**            | Defines bundle name                      | Every project                    |
| **include**           | Loads additional YAML files              | Split configuration              |
| **targets**           | Multiple deployment environments         | Dev / Test / Prod                |
| **workspace**         | Defines deployment workspace             | Different Databricks workspaces  |
| **variables**         | Reusable values                          | Cluster IDs, catalogs, schemas   |
| **variable defaults** | Default variable values                  | Environment-specific defaults    |
| **run_as**            | Execution identity                       | User or Service Principal        |
| **sync**              | Controls uploaded files                  | Exclude tests, docs, README      |
| **artifacts**         | Build Python wheels                      | Python package deployments       |
| **permissions**       | Configure access                         | Users and groups                 |
| **presets**           | Apply common settings                    | Naming conventions, prefixes     |
| **Git information**   | Deployment tracking                      | Audit and version control        |
| **scripts/hooks**     | Execute commands before/after deployment | Tests, notifications, automation |

---

# Learning Roadmap (Recommended Order)

| Priority | Topic                       | Difficulty   |
| -------- | --------------------------- | ------------ |
| ⭐⭐⭐⭐⭐    | Bundle                      | Beginner     |
| ⭐⭐⭐⭐⭐    | Include                     | Beginner     |
| ⭐⭐⭐⭐⭐    | Resources (Jobs, Pipelines) | Beginner     |
| ⭐⭐⭐⭐⭐    | Targets                     | Intermediate |
| ⭐⭐⭐⭐⭐    | Variables                   | Intermediate |
| ⭐⭐⭐⭐☆    | Sync                        | Intermediate |
| ⭐⭐⭐⭐☆    | Artifacts (Python Wheels)   | Intermediate |
| ⭐⭐⭐☆☆    | Permissions                 | Intermediate |
| ⭐⭐⭐☆☆    | Run As                      | Intermediate |
| ⭐⭐⭐☆☆    | Presets                     | Advanced     |
| ⭐⭐☆☆☆    | Git Metadata                | Advanced     |
| ⭐⭐☆☆☆    | Scripts/Hooks               | Advanced     |

This makes a good reference document for future Databricks Asset Bundle projects, and you can export it directly as a PDF.
