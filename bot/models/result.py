from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class Result:
    success: bool
    text: str = ""
    data: Optional[dict[str:Any]] = None

    def to_dict(self):
        return asdict(self)
