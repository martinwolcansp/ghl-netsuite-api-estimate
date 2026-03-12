import requests
from app.core.config import GHL_API_KEY, GHL_BASE_URL, GHL_PIPELINE_ID, GHL_STAGE_ID
import logging

logger = logging.getLogger("ghl_client")


def update_opportunity(opportunity_id, monetary_value, estimate_id, status="open"):
    """
    Actualiza una oportunidad en GHL con monto y custom field 'netsuite_estimate_id'.
    status: 'open', 'won' o 'lost'
    """
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

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