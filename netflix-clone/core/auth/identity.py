from dataclasses import dataclass
from typing import Literal


UserRole = Literal["user", "admin"]


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    role: UserRole
