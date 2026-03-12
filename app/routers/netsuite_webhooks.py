from fastapi import APIRouter, Request
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

        # Validación mínima de campos
        required_fields = ["estimateId", "opportunityId", "montoPresupuesto"]
        for field in required_fields:
            if field not in payload:
                return {"status": "error", "message": f"Falta el campo {field}"}

        # Conversión de tipos
        estimate_id = str(payload["estimateId"])  # GHL acepta string
        opportunity_id = str(payload["opportunityId"])
        monto = float(payload["montoPresupuesto"])

        result = sync_estimate_to_ghl(
            estimate_id,
            opportunity_id,
            monto
        )

        return {"status": "processed", "ghl_response": result}

    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return {"status": "error", "message": str(e)}