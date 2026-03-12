import logging
from app.clients.ghl_client import update_opportunity
from app.core.config import GHL_PIPELINE_ID, GHL_STAGE_ID

logger = logging.getLogger("ghl_service")


def sync_estimate_to_ghl(estimate_id, opportunity_id, monto, status="open"):
    """
    Sincroniza un estimate de NetSuite con una oportunidad en GHL.
    status puede ser 'open', 'won' o 'lost'
    """
    logger.info(f"Actualizando oportunidad {opportunity_id} en GHL con estimate {estimate_id}, monto {monto} y status {status}")

    result = update_opportunity(
        opportunity_id=opportunity_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        status=status
    )

    if "error" in result:
        logger.warning(f"No se pudo actualizar la oportunidad: {result['error']}")
    else:
        logger.info(f"Oportunidad actualizada exitosamente: {result}")

    return result