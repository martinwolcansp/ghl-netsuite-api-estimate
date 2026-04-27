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
# MAPEO NETSUITE → GHL (source of truth)
# ===============================
NS_TO_GHL = {
    "12": {"stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f", "status": "won"},
    "8":  {"stage_id": "ba115218-902b-4901-a90c-ec99c738d856", "status": "open"},
    "11": {"stage_id": "ba115218-902b-4901-a90c-ec99c738d856", "status": "open"},
    "10": {"stage_id": "ba115218-902b-4901-a90c-ec99c738d856", "status": "open"},
    "14": {"stage_id": "e2adaf6d-79d7-4dcc-ae0e-616f3e16d965", "status": "lost"},
    "18": {"stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f", "status": "won"},
    "13": {"stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f", "status": "won"},
}


# ===============================
# HELPERS
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
# MAIN SYNC
# ===============================
def sync_estimate_to_ghl(
    estimate_id,
    opportunity_id,
    monto,
    contact_id,
    estado_ns_id=None,
    es_manual=False,
    estado_ghl=None,
    pipeline_stage_id=None
):

    logger.info("===== SYNC NS → GHL =====")
    logger.info(f"estimate: {estimate_id}")
    logger.info(f"opp NS: {opportunity_id}")
    logger.info(f"estado_ns_id: {estado_ns_id}")
    logger.info(f"estado_ghl: {estado_ghl}")
    logger.info(f"es_manual: {es_manual}")

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
    # CURRENT STATE (for validation)
    # ===============================
    current_stage = matching.get("pipelineStageId")
    current_status = matching.get("status")
    current_value = matching.get("monetaryValue")

    # ===============================
    # DECISION TREE (FIXED PRIORITY)
    # ===============================
    stage_id = None
    status = None

    # 1. MANUAL override (estado GHL directo)
    if estado_ghl:
        status = normalize_status(estado_ghl)

        if status == "open":
            stage_id = "ba115218-902b-4901-a90c-ec99c738d856"
        elif status == "won":
            stage_id = "7068ac99-7f3a-4e57-ae7c-088acf5b629f"
        elif status == "lost":
            stage_id = "e2adaf6d-79d7-4dcc-ae0e-616f3e16d965"
        else:
            logger.warning(f"Invalid estado_ghl: {estado_ghl}")
            return {"error": "invalid_estado_ghl"}

    # 2. NS mapping (automatizado o manual con estado NS)
    elif estado_ns_id:
        mapping = NS_TO_GHL.get(str(estado_ns_id))

        if not mapping:
            logger.warning(f"NS state not mapped: {estado_ns_id}")
            return {"error": "state_not_mapped"}

        stage_id = mapping["stage_id"]
        status = mapping["status"]

    # 3. DEFAULT SAFE (automático)
    else:
        stage_id = "7068ac99-7f3a-4e57-ae7c-088acf5b629f"
        status = "won"

    # ===============================
    # VALIDACIÓN CRÍTICA (FIX ERROR 400)
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
        logger.error(f"INVALID STAGE SENT TO GHL: {stage_id}")
        return {
            "error": "invalid_stage",
            "stage_sent": stage_id
        }

    # ===============================
    # IDEMPOTENCY CHECK
    # ===============================
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

    return update_opportunity(
        opportunity_id=ghl_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        status=status,
        pipeline_stage_id=stage_id
    )