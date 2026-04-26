# routers/netsuite_webhooks.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

from app.services.ghl_service import sync_estimate_to_ghl

router = APIRouter(
    prefix="/webhook/netsuite",
    tags=["NetSuite Webhooks"]
)

logger = logging.getLogger("netsuite_webhooks")


@router.post("/estimate-approved")
async def estimate_approved(request: Request):

    try:

        payload = await request.json()

        logger.info("========== NETSUITE ESTIMATE APPROVED ==========")
        logger.info(f"Payload recibido: {payload}")

        required_fields = [
            "estimateId",
            "opportunityId",
            "montoPresupuesto",
            "contactIdGHL"
        ]

        for field in required_fields:
            if field not in payload:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": f"Falta el campo {field}"
                    }
                )

        estimate_id = str(payload["estimateId"])
        opportunity_id = str(payload["opportunityId"])
        monto = float(payload["montoPresupuesto"])
        contact_id = payload["contactIdGHL"]

        # 🔥 NUEVO: capturar estado
        estado_ghl = payload.get("estadoGHL")

        logger.info(f"Estado GHL recibido: {estado_ghl}")

        result = sync_estimate_to_ghl(
            estimate_id=estimate_id,
            opportunity_id=opportunity_id,
            monto=monto,
            contact_id=contact_id,
            estado_ghl=estado_ghl  # 🔥 CLAVE
        )

        if "error" in result:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "ghl_response": result
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "processed",
                "ghl_response": result
            }
        )

    except Exception as e:

        logger.error(f"Error procesando webhook: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )