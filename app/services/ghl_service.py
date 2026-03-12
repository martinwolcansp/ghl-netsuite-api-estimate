import logging
from app.clients.ghl_client import update_opportunity
from app.core.config import GHL_PIPELINE_ID, GHL_STAGE_ID

logger = logging.getLogger("ghl_service")

def sync_estimate_to_ghl(estimate_id, opportunity_id, monto):
    logger.info(f"Actualizando oportunidad {opportunity_id} en GHL con estimate {estimate_id} y monto {monto}")

    result = update_opportunity(
        opportunity_id=opportunity_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        pipeline_id=GHL_PIPELINE_ID,
        stage_id=GHL_STAGE_ID
    )

    if "error" in result:
        logger.warning(f"No se pudo actualizar la oportunidad: {result['error']}")
    else:
        logger.info(f"Oportunidad actualizada exitosamente: {result}")

    return result