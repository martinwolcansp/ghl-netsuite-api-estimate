import requests
from app.core.config import GHL_API_KEY, GHL_BASE_URL
import logging

logger = logging.getLogger("ghl_client")

def update_opportunity(opportunity_id, monetary_value, estimate_id):
    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }
    payload = {
        "monetaryValue": monetary_value,
        "customFields": [
            {
                "key": "netsuite_estimate_id",
                "field_value": str(estimate_id)
            }
        ]
    }

    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al actualizar oportunidad {opportunity_id}: {str(e)}")
        return {"error": str(e)}