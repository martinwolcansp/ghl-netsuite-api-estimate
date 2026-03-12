import logging
from app.clients.ghl_client import update_opportunity

logger = logging.getLogger("ghl_service")

def sync_estimate_to_ghl(estimate_id, opportunity_id, monto):
    logger.info(f"Actualizando oportunidad {opportunity_id} en GHL con estimate {estimate_id} y monto {monto}")
    
    result = update_opportunity(
        opportunity_id,
        monto,
        estimate_id
    )

    if "error" in result:
        logger.warning(f"No se pudo actualizar la oportunidad: {result['error']}")
    else:
        logger.info(f"Oportunidad actualizada exitosamente: {result}")

    return result