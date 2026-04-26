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
# MAPEO NETSUITE → GHL (ÚNICO SOURCE OF TRUTH)
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


def sync_estimate_to_ghl(
    estimate_id,
    opportunity_id,
    monto,
    contact_id,
    estado_ns_id=None,
    es_manual=False,
    estado_ghl=None
):

    logger.info("===== SYNC NS → GHL =====")
    logger.info(f"estimate: {estimate_id}")
    logger.info(f"opp NS: {opportunity_id}")
    logger.info(f"estado_ns_id: {estado_ns_id}")
    logger.info(f"es_manual: {es_manual}")

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
        return {"error": "not_found"}

    ghl_id = matching["id"]

    # ===============================
    # DECISIÓN DE NEGOCIO
    # ===============================
    if es_manual:
        mapping = NS_TO_GHL.get(str(estado_ns_id))
        if not mapping:
            return {"error": "state_not_mapped"}

        stage_id = mapping["stage_id"]
        status = mapping["status"]

    else:
        # AUTOMÁTICO: Compra → Ganado
        stage_id = "7068ac99-7f3a-4e57-ae7c-088acf5b629f"
        status = "won"

    # ===============================
    # VALIDACIÓN REAL (IMPORTANTE)
    # ===============================
    already = (
        str(matching.get("monetaryValue")) == str(monto)
        and matching.get("pipelineStageId") == stage_id
        and matching.get("status") == status
    )

    if already:
        logger.info("Sin cambios")
        return {"status": "already_updated"}

    return update_opportunity(
        opportunity_id=ghl_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        status=status,
        pipeline_stage_id=stage_id
    )