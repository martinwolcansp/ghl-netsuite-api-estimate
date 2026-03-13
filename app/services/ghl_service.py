# services/ghl_service.py
import logging
import requests

from app.clients.ghl_client import update_opportunity
from app.core.config import (
    GHL_API_KEY,
    GHL_LOCATION_ID,
    GHL_STAGE_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
)

logger = logging.getLogger("ghl_service")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


def sync_estimate_to_ghl(estimate_id, opportunity_id, monto, contact_id):

    logger.info("===== SINCRONIZANDO ESTIMATE NETSUITE → GHL =====")
    logger.info(f"contactId: {contact_id}")
    logger.info(f"opportunityId NS: {opportunity_id}")
    logger.info(f"estimateId: {estimate_id}")
    logger.info(f"monto: {monto}")

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }

    # ===============================
    # Buscar oportunidades del contacto
    # ===============================

    params = {
        "location_id": GHL_LOCATION_ID,
        "contact_id": contact_id
    }

    resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers=headers,
        params=params
    )

    if resp.status_code not in (200, 201):
        logger.error(f"Error buscando oportunidades: {resp.text}")
        return {"error": resp.text}

    data = resp.json()
    opportunities = data.get("opportunities", [])

    logger.info(f"Oportunidades encontradas para el contacto: {len(opportunities)}")

    matching_opportunity = None

    # ===============================
    # Filtrar por custom field NS
    # ===============================

    for opp in opportunities:

        for cf in opp.get("customFields", []):

            value = cf.get("fieldValue") or cf.get("fieldValueString")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                matching_opportunity = opp
                break

        if matching_opportunity:
            break

    if not matching_opportunity:
        logger.warning("No se encontró oportunidad que coincida con el valor de NetSuite.")
        return {"error": "Opportunity not found"}

    ghl_opportunity_id = matching_opportunity.get("id")

    monetary_value_actual = matching_opportunity.get("monetaryValue")
    pipeline_stage_actual = matching_opportunity.get("pipelineStageId")

    logger.info(f"Oportunidad encontrada: {ghl_opportunity_id}")
    logger.info(f"MonetaryValue actual: {monetary_value_actual}")
    logger.info(f"PipelineStage actual: {pipeline_stage_actual}")

    # ===============================
    # Validación para evitar doble update
    # ===============================

    if monetary_value_actual and pipeline_stage_actual == GHL_STAGE_ID:
        logger.info("La oportunidad ya fue actualizada previamente.")
        return {"status": "already_updated"}

    logger.info("Actualizando oportunidad en GHL...")

    result = update_opportunity(
        opportunity_id=ghl_opportunity_id,
        monetary_value=monto,
        estimate_id=estimate_id,
        status="won"
    )

    return result