import pytest
from orders.location import Location, Table, Volume


@pytest.fixture
def location():
    return Location(catalog="workspace", schema="orders_dev")


def test_table_is_fully_qualified(location):
    assert location.table(Table.BRONZE) == "workspace.orders_dev.orders_bronze"


def test_volume_is_a_volumes_path(location):
    assert location.volume(Volume.LANDING) == (
        "/Volumes/workspace/orders_dev/landing"
    )


def test_from_args_reads_named_parameters(location):
    argv = ["--catalog=workspace", "--schema=orders_dev"]

    assert Location.from_args(argv) == location


def test_from_args_requires_schema():
    with pytest.raises(SystemExit):
        Location.from_args(["--catalog=workspace"])
