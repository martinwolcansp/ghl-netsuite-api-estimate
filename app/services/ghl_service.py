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
# MAPEO DE NEGOCIO NS → GHL
# ===============================

NS_TO_GHL = {
    "12": {"stage": "Venta ganada", "status": "won"},
    "8": {"stage": "Presupuesto enviado", "status": "open"},
    "11": {"stage": "Presupuesto enviado", "status": "open"},
    "10": {"stage": "Presupuesto enviado", "status": "open"},
    "14": {"stage": "Venta perdida", "status": "lost"},
    "18": {"stage": "Venta ganada", "status": "won"},
    "13": {"stage": "Venta ganada", "status": "won"},
}


def sync_estimate_to_ghl(
    estimate_id,
    opportunity_id,
    monto,
    contact_id,
    estado_ns_id=None,
    es_manual=False
):

    logger.info("===== SINCRONIZANDO ESTIMATE NETSUITE → GHL =====")
    logger.info(f"contactId: {contact_id}")
    logger.info(f"opportunityId NS: {opportunity_id}")
    logger.info(f"estimateId: {estimate_id}")
    logger.info(f"monto: {monto}")
    logger.info(f"estado NS id: {estado_ns_id}")
    logger.info(f"es_manual: {es_manual}")

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

    opportunities = resp.json().get("opportunities", [])

    logger.info(f"Oportunidades encontradas: {len(opportunities)}")

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
        logger.warning("No se encontró oportunidad en GHL")
        return {"error": "not_found"}

    ghl_id = matching["id"]

    # ===============================
    # MAPPING FINAL
    # ===============================

    if es_manual:
        mapping = NS_TO_GHL.get(str(estado_ns_id))

        if not mapping:
            logger.warning("Estado NS no mapeado")
            return {"error": "state_not_mapped"}

        stage = mapping["stage"]
        status = mapping["status"]

    else:
        # AUTOMÁTICO (siempre Compra → Ganado)
        stage = "Venta ganada"
        status = "won"

    logger.info(f"Stage final: {stage}")
    logger.info(f"Status final: {status}")

    # ===============================
    # VALIDACIÓN INTELIGENTE
    # ===============================

    already_synced = (
        matching.get("monetaryValue") == monto
        and matching.get("status") == status
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
        pipeline_stage=stage
    )

    return result