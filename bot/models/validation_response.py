from dataclasses import dataclass, asdict
from typing import Literal, Optional


@dataclass
class SkinValidationResponse:
    hash_name: str
    status: Literal["success", "error"]
    text: Optional[str] = None

    def to_dict(self):
        return asdict(self)
