# app/routers/netsuite_webhooks.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import hmac
import logging
import time

from app.services.ghl_service import sync_estimate_to_ghl
from app.core.config import WEBHOOK_SECRET
from app import registro_eventos

router = APIRouter(prefix="/webhook/netsuite", tags=["NetSuite"])

logger = logging.getLogger("netsuite_webhooks")


def _detalle_error(result):
    """Texto corto del error para el registro de eventos."""
    error = result.get("error")
    partes = [str(error)]
    if result.get("status_code"):
        partes.append(f"HTTP {result['status_code']}")
    if result.get("response"):
        partes.append(str(result["response"])[:300])
    if result.get("stage_received"):
        partes.append(f"etapa recibida {result['stage_received']}")
    return " · ".join(partes)


@router.post("/estimate-approved")
async def estimate_approved(request: Request):

    inicio = time.monotonic()
    payload = None

    # ===============================
    # REGISTRO DE EVENTOS (pestaña En vivo)
    # ===============================
    # No cambia la respuesta: se escribe en segundo plano.
    def registrar(resultado, respuesta=None, detalle=None):
        referencia = payload.get("estimateId") if isinstance(payload, dict) else None
        registro_eventos.registrar(
            etapa="presupuesto",
            origen="netsuite",
            resultado=resultado,
            referencia_id=referencia,
            detalle=detalle,
            payload=payload,
            respuesta=respuesta,
            duracion_ms=int((time.monotonic() - inicio) * 1000),
        )

    # ===============================
    # SECRETO COMPARTIDO (servidor local)
    # ===============================
    # Sólo se exige si WEBHOOK_SECRET tiene valor. Acepta el header
    # X-Integration-Secret o el parámetro ?token=.
    if WEBHOOK_SECRET:
        recibido = (
            request.headers.get("X-Integration-Secret")
            or request.query_params.get("token")
            or ""
        )
        if not hmac.compare_digest(recibido, WEBHOOK_SECRET):
            logger.warning("Webhook rechazado: secreto ausente o inválido")
            registrar("rechazado", detalle="Secreto ausente o inválido")
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized"}
            )

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
                contenido = {"error": f"Falta campo requerido: {field}"}
                registrar("error", contenido, contenido["error"])
                return JSONResponse(
                    status_code=400,
                    content=contenido
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
            contenido = {"status": "error", "detail": result}
            registrar("error", contenido, _detalle_error(result))
            return JSONResponse(
                status_code=400,
                content=contenido
            )

        contenido = {
            "status": "ok",
            "result": result
        }

        if result.get("status") == "already_updated":
            registrar("already_updated", contenido)
        elif result.get("simulado"):
            registrar("simulado", contenido)
        else:
            registrar("updated", contenido)

        return contenido

    except Exception as e:
        logger.error(f"ERROR WEBHOOK: {str(e)}")
        registrar("error", {"error": str(e)}, str(e))

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
