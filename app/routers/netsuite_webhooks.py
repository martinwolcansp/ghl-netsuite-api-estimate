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

        logger.info("========== NETSUITE WEBHOOK ==========")
        logger.info(f"Payload recibido: {payload}")

        # ===============================
        # VALIDACIÓN BÁSICA
        # ===============================
        required_fields = [
            "estimateId",
            "opportunityId",
            "montoPresupuesto",
            "contactIdGHL",
            "estadoGHL",
            "pipelineStageId"
        ]

        for field in required_fields:
            if field not in payload:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Falta campo requerido: {field}"}
                )

        # ===============================
        # NORMALIZACIÓN
        # ===============================
        estimate_id = str(payload["estimateId"])
        opportunity_id = str(payload["opportunityId"])
        monto = float(payload["montoPresupuesto"])
        contact_id = payload["contactIdGHL"]

        estado_ghl = payload["estadoGHL"]
        pipeline_stage_id = payload["pipelineStageId"]

        logger.info(f"Estado GHL: {estado_ghl}")
        logger.info(f"Stage ID: {pipeline_stage_id}")

        # ===============================
        # CALL SERVICE (SIN LÓGICA)
        # ===============================
        result = sync_estimate_to_ghl(
            estimate_id=estimate_id,
            opportunity_id=opportunity_id,
            monto=monto,
            contact_id=contact_id,
            estado_ghl=estado_ghl,
            pipeline_stage_id=pipeline_stage_id
        )

        if "error" in result:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": result}
            )

        return {
            "status": "ok",
            "result": result
        }

    except Exception as e:
        logger.error(f"ERROR WEBHOOK: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )