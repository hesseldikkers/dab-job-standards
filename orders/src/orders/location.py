import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class Table(StrEnum):
    BRONZE = "orders_bronze"
    SILVER = "orders_silver"


class Volume(StrEnum):
    LANDING = "landing"
    CHECKPOINTS = "checkpoints"


@dataclass(frozen=True)
class Location:
    catalog: str
    schema: str

    def table(self, name: Table) -> str:
        return f"{self.catalog}.{self.schema}.{name}"

    def volume(self, name: Volume) -> str:
        return f"/Volumes/{self.catalog}/{self.schema}/{name}"

    @classmethod
    def from_args(cls, argv: Sequence[str] | None = None) -> "Location":
        parser = argparse.ArgumentParser()
        parser.add_argument("--catalog", required=True)
        parser.add_argument("--schema", required=True)
        return cls(**vars(parser.parse_args(argv)))
