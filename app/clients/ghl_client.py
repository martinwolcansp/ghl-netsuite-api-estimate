# clients/ghl_client.py

import requests
import logging
from app.core.config import GHL_API_KEY, GHL_BASE_URL

logger = logging.getLogger("ghl_client")


def map_status(estado):
    mapping = {
        "open": "open",
        "Abierto": "open",
        "Ganado": "won",
        "Perdido": "lost",
        "won": "won",
        "lost": "lost"
    }
    return mapping.get(estado, "open")


def update_opportunity(
    opportunity_id,
    monetary_value,
    estimate_id,
    status=None,
    pipeline_stage=None
):
    """
    Actualiza oportunidad en GHL correctamente:
    - status: open / won / lost
    - pipeline_stage: stageId real del pipeline
    """

    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

    # ===============================
    # NORMALIZACIÓN
    # ===============================

    status_final = map_status(status)

    payload = {
        "status": status_final,
        "monetaryValue": monetary_value,
        "customFields": [
            {
                "key": "netsuite_estimate_id",
                "field_value": str(estimate_id)
            }
        ]
    }

    # 🔥 SOLO si viene stage lo aplicamos
    if pipeline_stage:
        payload["pipelineStageId"] = pipeline_stage

    logger.info(f"Payload GHL FINAL: {payload}")

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        result = response.json()

        logger.info(
            f"Oportunidad {opportunity_id} actualizada OK | "
            f"status={status_final} | stage={pipeline_stage}"
        )

        return result

    except requests.RequestException as e:
        logger.error(f"Error GHL update: {str(e)}")
        return {"error": str(e)}