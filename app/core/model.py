from dataclasses import dataclass
from typing import List

@dataclass
class ObjectiveFunction:
    coefficients: List[float]
    mode: str  # "max" o "min"


@dataclass
class Constraint:
    coefficients: List[float]
    sign: str   # "<=", ">=", "="
    value: float


@dataclass
class LinearProgram:
    objective: ObjectiveFunction
    constraints: List[Constraint]
    variables: int