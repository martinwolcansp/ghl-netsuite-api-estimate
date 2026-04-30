#app/service/ghl_service.py

import logging
import requests

from app.clients.ghl_client import update_opportunity
from app.core.config import (
    GHL_API_KEY,
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_service")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# NORMALIZACIÓN STATUS
# ===============================
def normalize_status(value: str):
    if not value:
        return None

    value = value.lower().strip()

    if value in ["abierto", "open"]:
        return "open"
    if value in ["ganado", "won"]:
        return "won"
    if value in ["perdido", "lost"]:
        return "lost"

    return None


# ===============================
# MAIN SYNC (SIN LÓGICA DE NEGOCIO)
# ===============================
def sync_estimate_to_ghl(
    estimate_id,
    opportunity_id,
    monto,
    contact_id,
    estado_ghl,
    pipeline_stage_id
):

    logger.info("===== SYNC NS → GHL =====")
    logger.info(f"estimate: {estimate_id}")
    logger.info(f"opp NS: {opportunity_id}")
    logger.info(f"estado_ghl: {estado_ghl}")
    logger.info(f"pipeline_stage_id: {pipeline_stage_id}")

    # ===============================
    # NORMALIZACIÓN
    # ===============================
    status = normalize_status(estado_ghl)

    if not status:
        logger.error(f"Estado GHL inválido: {estado_ghl}")
        return {"error": "invalid_estado_ghl"}

    stage_id = pipeline_stage_id

    # ===============================
    # VALIDACIÓN STAGE (ANTI-400)
    # ===============================
    VALID_STAGES = {
        "71989c58-aeee-4c5a-bfc6-02997375065b",
        "5dc95c7f-0b33-4a04-aa45-d078cc571920",
        "3bcc1dd2-70de-47af-b123-2aaa6e6bc818",
        "ba115218-902b-4901-a90c-ec99c738d856",
        "7068ac99-7f3a-4e57-ae7c-088acf5b629f",
        "e2adaf6d-79d7-4dcc-ae0e-616f3e16d965"
    }

    if stage_id not in VALID_STAGES:
        logger.error(f"INVALID STAGE FROM NETSUITE: {stage_id}")
        return {
            "error": "invalid_stage",
            "stage_received": stage_id
        }

    # ===============================
    # SEARCH OPPORTUNITY
    # ===============================
    resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Accept": "application/json",
            "Version": "2021-07-28"
        },
        params={
            "location_id": GHL_LOCATION_ID,
            "contact_id": contact_id
        }
    )

    if resp.status_code not in (200, 201):
        logger.error(f"GHL search error: {resp.text}")
        return {"error": resp.text}

    opportunities = resp.json().get("opportunities", [])

    matching = None

    for opp in opportunities:
        for cf in opp.get("customFields", []):
            value = cf.get("fieldValue") or cf.get("fieldValueString")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                matching = opp
                break

        if matching:
            break

    if not matching:
        logger.warning("Opportunity not found in GHL")
        return {"error": "not_found"}

    ghl_id = matching["id"]

    # ===============================
    # IDEMPOTENCY CHECK
    # ===============================
    current_stage = matching.get("pipelineStageId")
    current_status = matching.get("status")
    current_value = matching.get("monetaryValue")

    already = (
        str(current_value) == str(monto)
        and current_stage == stage_id
        and current_status == status
    )

    if already:
        logger.info("No changes detected (idempotent)")
        return {"status": "already_updated"}

    # ===============================
    # UPDATE
    # ===============================
    logger.info(f"FINAL UPDATE → stage={stage_id} status={status}")

    #return update_opportunity(
    #    opportunity_id=ghl_id,
    #    monetary_value=monto,
    #    estimate_id=estimate_id,
    #    status=status,
    #    pipeline_stage_id=stage_id
    #)

    payload = {
        "monetaryValue": monto,
        "status": status,
        "pipelineStageId": stage_id,
        "estimateId": estimate_id
    }

    return update_opportunity(
        opportunity_id=ghl_id,
        payload=payload
    )