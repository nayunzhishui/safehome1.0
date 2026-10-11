"""Compatibility shim for the former Task37-named computation contract service.

Runtime code should import :mod:`services.computation_contract_service`.
This module remains temporarily so historical tests and scripts keep working.
"""

from services.computation_contract_service import (  # noqa: F401
    ContractError,
    PATH,
    public_status,
    read_record,
    registry,
    validate_new_record,
)

__all__ = [
    "ContractError",
    "PATH",
    "registry",
    "validate_new_record",
    "read_record",
    "public_status",
]
