from dataclasses import replace

from databricks.bundles.core import Bundle, job_mutator
from databricks.bundles.jobs import (
    Job,
    JobEmailNotifications,
    JobEnvironment,
)

ENVIRONMENT_VERSION = "6"
ALERT_EMAIL = "orders-team@example.com"


@job_mutator
def add_defaults(bundle: Bundle, job: Job) -> Job:
    return replace(
        job,
        email_notifications=_with_failure_email(job.email_notifications),
        environments=[_with_version(e) for e in job.environments],
    )


@job_mutator
def require_owner(bundle: Bundle, job: Job) -> Job:
    if "owner" not in job.tags:
        raise ValueError(
            f'Job "{job.name}" has no "owner" tag. '
            'Add the tag "owner" to the job in its resource file.'
        )
    return job


def _with_failure_email(
    notifications: JobEmailNotifications | None,
) -> JobEmailNotifications:
    notifications = notifications or JobEmailNotifications()
    if notifications.on_failure:
        return notifications
    return replace(notifications, on_failure=[ALERT_EMAIL])


def _with_version(env: JobEnvironment) -> JobEnvironment:
    if env.spec is None or env.spec.environment_version:
        return env
    spec = replace(env.spec, environment_version=ENVIRONMENT_VERSION)
    return replace(env, spec=spec)
