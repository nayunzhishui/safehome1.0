"""Compatibility route for the computation-contract public status endpoint.

The URL is already domain based (``/api/research/computation-contract``), so
only the Python filename remains historical. New runtime logic lives in the
generic computation-contract service.
"""

from flask import Blueprint

from routes.utils import fail, ok
from services.computation_contract_service import ContractError, public_status


bp = Blueprint("task37_contracts", __name__, url_prefix="/api/research/computation-contract")


@bp.get("/public-status")
def get_public_status():
    try:
        return ok(public_status())
    except ContractError as exc:
        return fail(exc.code, str(exc), status=503)
