# app/clients/ghl_client.py

import requests
import logging
from app.core.config import GHL_API_KEY, GHL_BASE_URL

logger = logging.getLogger("ghl_client")


# ===============================
# NORMALIZACIÓN STATUS
# ===============================
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


# ===============================
# VALIDACIÓN BÁSICA
# ===============================
def validate_payload(payload):
    errors = []

    if "status" in payload:
        if payload["status"] not in ["open", "won", "lost"]:
            errors.append(f"Invalid status: {payload['status']}")

    if "pipelineStageId" in payload:
        if not isinstance(payload["pipelineStageId"], str):
            errors.append("pipelineStageId must be string")

    if "monetaryValue" in payload:
        try:
            float(payload["monetaryValue"])
        except Exception:
            errors.append("monetaryValue must be numeric")

    return errors


# ===============================
# UPDATE OPPORTUNITY (UNIFICADO)
# ===============================
def update_opportunity(opportunity_id, payload):

    url = f"{GHL_BASE_URL}/opportunities/{opportunity_id}"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Version": "2021-07-28"
    }

    # ===============================
    # NORMALIZACIÓN STATUS
    # ===============================
    if "status" in payload:
        payload["status"] = map_status(payload["status"])

    # ===============================
    # LOG DEBUG
    # ===============================
    logger.info("========== GHL UPDATE REQUEST ==========")
    logger.info(f"Opportunity ID: {opportunity_id}")
    logger.info(f"Payload: {payload}")

    # ===============================
    # VALIDACIÓN
    # ===============================
    validation_errors = validate_payload(payload)

    if validation_errors:
        logger.error("PAYLOAD VALIDATION FAILED")
        for err in validation_errors:
            logger.error(f" - {err}")
        return {"error": "validation_failed", "details": validation_errors}

    # ===============================
    # REQUEST
    # ===============================
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)

        logger.info(f"GHL RESPONSE STATUS: {response.status_code}")
        logger.info(f"GHL RESPONSE BODY: {response.text}")

        if response.status_code >= 400:
            return {
                "error": "ghl_rejected",
                "status_code": response.status_code,
                "response": response.text,
                "sent_payload": payload
            }

        return response.json()

    except requests.RequestException as e:
        logger.error("REQUEST FAILED")
        logger.error(str(e))

        return {
            "error": "request_failed",
            "message": str(e),
            "sent_payload": payload
        }