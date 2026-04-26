import requests
import logging
from app.core.config import GHL_API_KEY, GHL_BASE_URL

logger = logging.getLogger("ghl_client")


def map_status(status):
    mapping = {
        "open": "open",
        "Abierto": "open",
        "Ganado": "won",
        "Perdido": "lost",
        "won": "won",
        "lost": "lost"
    }
    return mapping.get(status, "open")


def update_opportunity(
    opportunity_id,
    monetary_value,
    estimate_id,
    status=None,
    pipeline_stage_id=None
):
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

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

    # 🔥 stage SOLO si viene definido
    if pipeline_stage_id:
        payload["pipelineStageId"] = pipeline_stage_id

    logger.info(f"Payload GHL: {payload}")

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        logger.info(
            f"OK update opp {opportunity_id} | status={status_final} | stage={pipeline_stage_id}"
        )

        return response.json()

    except requests.RequestException as e:
        logger.error(f"GHL update error: {str(e)}")
        return {"error": str(e)}