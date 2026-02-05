from dataclasses import dataclass


@dataclass
class StockResult:
    variant_name: str
    is_available: bool
    url: str
