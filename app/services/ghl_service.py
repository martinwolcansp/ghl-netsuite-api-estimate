# services/ghl_service.py

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
# MAPEO NETSUITE → GHL (REAL)
# ===============================
NS_TO_GHL = {
    "12": {
        "stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f",  # Venta ganada
        "status": "won"
    },
    "8": {
        "stage_id": "ba115218-902b-4e57-ae7c-088acf5b629f",  # Presupuesto enviado
        "status": "open"
    },
    "11": {
        "stage_id": "ba115218-902b-4e57-ae7c-088acf5b629f",
        "status": "open"
    },
    "10": {
        "stage_id": "ba115218-902b-4e57-ae7c-088acf5b629f",
        "status": "open"
    },
    "14": {
        "stage_id": "e2adaf6d-79d7-4dcc-ae0e-616f3e16d965",  # Venta perdida
        "status": "lost"
    },
    "18": {
        "stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f",
        "status": "won"
    },
    "13": {
        "stage_id": "7068ac99-7f3a-4e57-ae7c-088acf5b629f",
        "status": "won"
    },
}


def sync_estimate_to_ghl(
    estimate_id,
    opportunity_id,
    monto,
    contact_id,
    estado_ns_id=None,
    es_manual=False
):

    logger.info("===== NETSUITE → GHL SYNC =====")
    logger.info(f"estimateId: {estimate_id}")
    logger.info(f"opportunityId NS: {opportunity_id}")
    logger.info(f"monto: {monto}")
    logger.info(f"estado_ns_id: {estado_ns_id}")
    logger.info(f"es_manual: {es_manual}")

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }

    # ===============================
    # Buscar oportunidades por contacto
    # ===============================
    resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers=headers,
        params={
            "location_id": GHL_LOCATION_ID,
            "contact_id": contact_id
        }
    )

    if resp.status_code not in (200, 201):
        logger.error(f"Error buscando oportunidades: {resp.text}")
        return {"error": resp.text}

    opportunities = resp.json().get("opportunities", [])

    logger.info(f"Oportunidades encontradas: {len(opportunities)}")

    matching = None

    # ===============================
    # Match por NetSuite ID
    # ===============================
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
        logger.warning("No se encontró oportunidad en GHL")
        return {"error": "not_found"}

    ghl_id = matching["id"]

    monetary_actual = matching.get("monetaryValue")
    stage_actual = matching.get("pipelineStageId")
    status_actual = matching.get("status")

    logger.info(f"GHL Opportunity: {ghl_id}")
    logger.info(f"Stage actual: {stage_actual}")
    logger.info(f"Status actual: {status_actual}")

    # ===============================
    # MAPEO FINAL
    # ===============================
    if es_manual:

        mapping = NS_TO_GHL.get(str(estado_ns_id))

        if not mapping:
            logger.warning("Estado NS no mapeado")
            return {"error": "state_not_mapped"}

        stage_id = mapping["stage_id"]
        status = mapping["status"]

    else:
        # AUTOMÁTICO: siempre compra → ganada
        stage_id = "7068ac99-7f3a-4e57-ae7c-088acf5b629f"
        status = "won"

    logger.info(f"Stage final: {stage_id}")
    logger.info(f"Status final: {status}")

    # ===============================
    # VALIDACIÓN REAL
    # ===============================
    already_synced = (
        str(monetary_actual) == str(monto)
        and stage_actual == stage_id
        and status_actual == status
    )

    if already_synced:
        logger.info("Sin cambios detectados")
        return {"status": "already_updated"}

    # ===============================
    # UPDATE
    # ===============================
    result = update_opportunity(
        opportunity_id=ghl_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        status=status,
        pipeline_stage_id=stage_id
    )

    return result