from fastapi import APIRouter, Request
import logging

router = APIRouter(
    prefix="/webhook/netsuite",
    tags=["NetSuite Webhooks"]
)

logger = logging.getLogger("netsuite_webhooks")


@router.post("/estimate-approved")
async def estimate_approved(request: Request):

    try:

        payload = await request.json()
        headers = dict(request.headers)

        logger.info("========== NETSUITE ESTIMATE APPROVED ==========")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {payload}")

        return {
            "status": "received",
            "event": "estimate-approved",
            "payload": payload
        }

    except Exception as e:

        logger.error(f"Error procesando webhook NetSuite: {str(e)}")

        return {
            "status": "error",
            "message": str(e)
        }