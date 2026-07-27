"""Read-only public summary for the Task 37 computation contract."""

from flask import Blueprint

from routes.utils import fail, ok
from services.task37_contract_service import ContractError, public_status


bp = Blueprint("task37_contracts", __name__, url_prefix="/api/research/computation-contract")


@bp.get("/public-status")
def get_public_status():
    try:
        return ok(public_status())
    except ContractError as exc:
        return fail(exc.code, str(exc), status=503)
