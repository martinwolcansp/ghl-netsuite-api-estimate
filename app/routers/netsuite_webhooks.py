from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

from app.services.ghl_service import sync_estimate_to_ghl

router = APIRouter(prefix="/webhook/netsuite", tags=["NetSuite"])

logger = logging.getLogger("netsuite_webhooks")


@router.post("/estimate-approved")
async def estimate_approved(request: Request):

    try:
        payload = await request.json()

        logger.info(f"Payload: {payload}")

        estimate_id = str(payload["estimateId"])
        opportunity_id = str(payload["opportunityId"])
        monto = float(payload["montoPresupuesto"])
        contact_id = payload["contactIdGHL"]

        estado_ns_id = payload.get("estadoNsId")
        es_manual = payload.get("esManual", False)
        estado_ghl = payload.get("estadoGHL")

        result = sync_estimate_to_ghl(
            estimate_id=estimate_id,
            opportunity_id=opportunity_id,
            monto=monto,
            contact_id=contact_id,
            estado_ns_id=estado_ns_id,
            es_manual=es_manual,
            estado_ghl=estado_ghl
        )

        return {"status": "ok", "result": result}

    except Exception as e:
        logger.error(str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})