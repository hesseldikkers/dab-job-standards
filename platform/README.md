# Platform bundle

Workspace components shared by all bundles, deployed as a separate
bundle. It currently holds one cluster policy per target.

| Target | Policy |
| --- | --- |
| `dev` | `job-compute-dev` |
| `acc` | `job-compute-acc` |
| `prd` | `job-compute-prd` |

Any bundle with classic compute can use a policy by looking it up
by name. The `weather` bundle does this through the `job_policy`
variable. Deploy this bundle first, per target:

```bash
cd platform
databricks bundle validate --strict -t dev -p <profile>
databricks bundle deploy -t dev -p <profile>
```

Without the policy, validating the `weather` bundle fails. Passing
`--var job_policy=<policy-id>` skips the lookup.

Permissions live in `config/grants.yml`, set per target through the
`policy_permissions` variable.

The policies have `prevent_destroy`, so `bundle destroy` refuses to
remove them. The node types are Azure examples; adjust them for your
cloud and check quota in your region.

Databricks Free Edition has serverless compute only. The policy
syntax validates there, but the policy has not been deployed or used
by a classic cluster.
