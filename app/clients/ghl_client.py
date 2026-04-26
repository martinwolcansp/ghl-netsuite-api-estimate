# clients/ghl_client.py

import requests
from app.core.config import GHL_API_KEY, GHL_BASE_URL, GHL_PIPELINE_ID, GHL_STAGE_ID
import logging

logger = logging.getLogger("ghl_client")


def map_estado_to_status(estado):
    mapping = {
        "Abierto": "open",
        "Ganado": "won",
        "Perdido": "lost"
    }
    return mapping.get(estado)


def update_opportunity(opportunity_id, monetary_value, estimate_id, estado_ghl=None):
    """
    Actualiza una oportunidad en GHL
    """

    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

    # 🔥 NUEVO: determinar status correctamente
    status = map_estado_to_status(estado_ghl)

    if not status:
        logger.warning(f"Estado no mapeado, usando default OPEN: {estado_ghl}")
        status = "open"

    payload = {
        "pipelineId": GHL_PIPELINE_ID,
        "pipelineStageId": GHL_STAGE_ID,
        "status": status,
        "monetaryValue": monetary_value,
        "customFields": [
            {
                "key": "netsuite_estimate_id",
                "field_value": str(estimate_id)
            }
        ]
    }

    logger.info(f"Estado recibido NS: {estado_ghl} → status GHL: {status}")
    logger.info(f"Enviando payload a GHL: {payload}")

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        logger.info(f"Oportunidad {opportunity_id} actualizada correctamente en GHL: {result}")
        return result

    except requests.RequestException as e:
        logger.error(f"Error al actualizar oportunidad {opportunity_id}: {str(e)}")
        return {"error": str(e)}