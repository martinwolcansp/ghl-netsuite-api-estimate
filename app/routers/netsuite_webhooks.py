from fastapi import APIRouter, Request
import logging

router = APIRouter(prefix="/webhook/netsuite", tags=["NetSuite Webhooks"])

logger = logging.getLogger("netsuite_webhooks")


@router.post("/estimate-approved-test")
async def estimate_approved_test(request: Request):

    try:

        payload = await request.json()
        headers = dict(request.headers)

        logger.info("========== NETSUITE WEBHOOK RECIBIDO ==========")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {payload}")

        return {
            "status": "received",
            "payload": payload
        }

    except Exception as e:

        logger.error(f"Error procesando webhook NetSuite: {str(e)}")

        return {
            "status": "error",
            "message": str(e)
        }