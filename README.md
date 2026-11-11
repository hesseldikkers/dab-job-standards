# dab-job-standards

Example Declarative Automation Bundles: a medallion architecture, a
classic-compute job from another team and the workspace policies
they share. Companion repository for the article
[Where to put Databricks job standards in a DAB](https://hd-engineer.pages.dev/blog/preset-mutator-or-policy/).

One repository, one folder per bundle. Each bundle has its own
`databricks.yml`, its own Python project (`pyproject.toml`,
`uv.lock`, `.venv`) and deploys on its own.

| Bundle | Owner | Compute |
| --- | --- | --- |
| `orders/` | orders team | serverless, SQL warehouse |
| `weather/` | forecasting team | classic, from a cluster policy |
| `platform/` | platform team | none; holds the cluster policies |

| Job | Bundle | What it does | Starts on |
| --- | --- | --- | --- |
| `orders_bronze` | `orders` | Auto Loader ingest from a volume | cron, daily 06:00 |
| `orders_silver` | `orders` | Standardize types, keep latest order version | update of `orders_bronze` |
| `orders_gold` | `orders` | SQL mart `orders_daily` | update of `orders_silver` |
| `weather_ingest` | `weather` | Load station observations from a volume | cron, daily 05:00 |

`weather_ingest` needs classic compute and does not run on
Databricks Free Edition. Its cluster settings come from a cluster
policy that the `platform` bundle deploys; see `platform/`.

## Prerequisites

- Databricks CLI 1.23.0
- [uv](https://docs.astral.sh/uv/)
- Java 17 for the local Spark tests (the first `orders` run
  downloads the Delta jars from Maven Central)
- `orders`, per target: schema `orders_<env>` in catalog
  `workspace`, with the volumes `landing` (raw JSON in
  `sales_orders/`) and `checkpoints`
- `weather`, per target: schema `weather_<env>` with the volume
  `landing` (JSON in `observations/`)

## Quick start

From the folder of a bundle (`orders` or `weather`):

```bash
uv sync
uv run pytest
databricks bundle validate --strict -t dev -p <profile>
databricks bundle plan -t dev -p <profile>
```

## Project structure

```
orders/                 # bundle: bronze, silver, gold
  databricks.yml        # bundle, variables, targets
  resources/            # <name>.<type>.yml, one file per resource
  mutators.py           # deploy-time standards (Python mutators)
  src/orders/           # all logic; tasks only call it
  tests/                # pytest unit tests
  pyproject.toml        # package, dev dependencies, pytest config
weather/                # bundle: one classic job; same layout
platform/               # bundle: workspace components (policies)
ruff.toml               # lint config shared by all bundles
.sqlfluff               # SQL lint config
.pre-commit-config.yaml # ruff and sqlfluff hooks
.github/workflows/      # CI (pull requests) and deploy (main)
```

## Targets

Every bundle has the same targets.

| Target | Mode | Runs as | Deployed by |
| --- | --- | --- | --- |
| `dev` | development | you | you |
| `acc` | production | run-as principal | pipeline |
| `prd` | production | run-as principal | pipeline, `main` only |

The schema per target is `<bundle>_<env>`, for example
`orders_acc`.

Principals and groups are placeholders (`<deploy-sp-id>`,
`<run-as-sp-id>`, `<data-engineers>`). The pipeline sets the real
values.

The bundles have no `workspace.host`. Locally pass `-p <profile>`;
in CI set `DATABRICKS_HOST`. The CLI fails when a profile host
differs from a host set in the YAML, and `workspace.host` does not
accept variables.

## CI/CD

| Workflow | Runs on | Steps |
| --- | --- | --- |
| `ci.yml` | pull request | prek (all files); pytest per bundle; per bundle `validate --strict -t acc` and `plan -t acc` (artifact) |
| `deploy.yml` | push to `main` | `deploy -t acc`, then `deploy -t prd` after approval; per target `orders`, then `platform`, then `weather` |

`weather` looks up the policy that `platform` deploys, so `platform`
deploys first. `orders` depends on neither.

The workflows log in with workload identity federation (OIDC), so
the repository holds no Databricks secrets. One-time setup:

1. In GitHub, create the environments `acc` and `prd`. On `prd`, add
   required reviewers and allow deployments from `main` only.
2. Set `DATABRICKS_HOST` as a repository variable, and
   `DEPLOY_SP_ID` and `RUN_AS_SP_ID` per environment. Without
   `DATABRICKS_HOST`, the Databricks jobs are skipped.
3. In Databricks, create one federation policy per environment on
   the deploy principal. Use the issuer
   `https://token.actions.githubusercontent.com` and the subject
   `repo:<org>/<repo>:environment:<env>`.

The deploy principal deploys; the run-as principal runs the `acc`
and `prd` jobs.

## Common tasks

Run from the folder of the bundle.

| Task | Command |
| --- | --- |
| Install | `uv sync` |
| Unit tests | `JAVA_HOME=$(brew --prefix openjdk@17) uv run pytest` |
| Validate | `databricks bundle validate --strict -t <target>` |
| Preview changes | `databricks bundle plan -t <target>` |

From the repository root:

| Task | Command |
| --- | --- |
| Lint (ruff, sqlfluff) | `uvx prek@0.5.9 run --all-files` |
| Run checks on every commit | `uvx prek@0.5.9 install` |

## Troubleshooting

- **Triggers do not fire in `dev`.** Development mode pauses
  schedules and triggers. Run the jobs by hand, in order.
- **Nothing downstream runs on a new target.** The silver and gold
  triggers watch tables that the earlier jobs create. Run bronze
  first.
- **`deploy` of `weather` fails with "Only serverless compute is
  supported".** Free Edition rejects classic jobs. Deploy `orders`
  only; it has no classic compute.
- **`validate -t acc` fails on the root path.** The path belongs to
  the deploy principal. Locally pass
  `--var deploy_sp=<your-user-name>`. The `platform` bundle needs
  the same override for every target. With `--strict` a warning
  about folder permissions remains; leave `--strict` out locally.
- **`validate` of `weather` fails with "Policy named
  'job-compute-...' does not exist".** Deploy the `platform` bundle
  first, or pass `--var job_policy=<policy-id>`.
- **`uv` warns that `VIRTUAL_ENV` does not match the project
  environment.** An environment from another project is active. Run
  `deactivate`; `uv` uses the `.venv` of the bundle folder.
