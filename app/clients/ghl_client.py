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
# VALIDACIÓN BÁSICA DE PAYLOAD
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
# UPDATE OPPORTUNITY (DEBUG MODE)
# ===============================
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

    # ===============================
    # NORMALIZACIÓN
    # ===============================
    status_final = map_status(status)

    payload = {
        "status": status_final,
        "monetaryValue": float(monetary_value),
        "customFields": [
            {
                "key": "netsuite_estimate_id",
                "field_value": str(estimate_id)
            }
        ]
    }

    if pipeline_stage_id:
        payload["pipelineStageId"] = pipeline_stage_id

    # ===============================
    # LOG DETALLADO (CLAVE DEBUG)
    # ===============================
    logger.info("========== GHL UPDATE REQUEST ==========")
    logger.info(f"Opportunity ID: {opportunity_id}")
    logger.info(f"Status raw: {status} → normalized: {status_final}")
    logger.info(f"Pipeline Stage ID: {pipeline_stage_id}")
    logger.info(f"Monetary Value: {monetary_value}")
    logger.info(f"Full Payload: {payload}")

    # ===============================
    # VALIDACIÓN PRE-REQUEST
    # ===============================
    validation_errors = validate_payload(payload)

    if validation_errors:
        logger.error("PAYLOAD VALIDATION FAILED:")
        for err in validation_errors:
            logger.error(f" - {err}")
        return {"error": "validation_failed", "details": validation_errors}

    # ===============================
    # REQUEST
    # ===============================
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)

        # ===============================
        # DEBUG REAL DE GHL (CLAVE)
        # ===============================
        logger.info(f"GHL RESPONSE STATUS: {response.status_code}")
        logger.info(f"GHL RESPONSE BODY: {response.text}")

        if response.status_code >= 400:
            logger.error("GHL REJECTED REQUEST")
            return {
                "error": "ghl_rejected",
                "status_code": response.status_code,
                "response": response.text,
                "sent_payload": payload
            }

        result = response.json()

        logger.info(
            f"SUCCESS update opp {opportunity_id} | "
            f"status={status_final} | stage={pipeline_stage_id}"
        )

        return result

    except requests.RequestException as e:
        logger.error("REQUEST FAILED")
        logger.error(str(e))

        return {
            "error": "request_failed",
            "message": str(e),
            "sent_payload": payload
        }