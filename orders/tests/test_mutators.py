import pytest
from databricks.bundles.core import Bundle
from databricks.bundles.jobs import (
    Environment,
    Job,
    JobEmailNotifications,
    JobEnvironment,
)
from mutators import (
    ALERT_EMAIL,
    ENVIRONMENT_VERSION,
    add_defaults,
    require_owner,
)

BUNDLE = Bundle(target="dev")


def test_require_owner_passes_job_with_owner():
    job = Job(name="orders_gold", tags={"owner": "orders-team"})

    assert require_owner.function(BUNDLE, job) == job


def test_require_owner_rejects_job_without_owner():
    job = Job(name="orders_gold", tags={"layer": "gold"})

    with pytest.raises(ValueError, match='"orders_gold" has no "owner"'):
        require_owner.function(BUNDLE, job)


def test_add_defaults_adds_failure_email():
    job = add_defaults.function(BUNDLE, Job())

    assert job.email_notifications.on_failure == [ALERT_EMAIL]


def test_add_defaults_keeps_own_failure_email():
    own = JobEmailNotifications(on_failure=["me@example.com"])

    job = add_defaults.function(BUNDLE, Job(email_notifications=own))

    assert job.email_notifications.on_failure == ["me@example.com"]


def test_add_defaults_sets_environment_version():
    env = JobEnvironment(environment_key="default", spec=Environment())

    job = add_defaults.function(BUNDLE, Job(environments=[env]))

    assert job.environments[0].spec.environment_version == (
        ENVIRONMENT_VERSION
    )


def test_add_defaults_keeps_own_environment_version():
    spec = Environment(environment_version="4")
    env = JobEnvironment(environment_key="default", spec=spec)

    job = add_defaults.function(BUNDLE, Job(environments=[env]))

    assert job.environments[0].spec.environment_version == "4"
