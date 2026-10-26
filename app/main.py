from fastapi import FastAPI
import logging

from app.routers import netsuite_webhooks
from app.core.config import MODO_SIMULACION, WEBHOOK_SECRET

# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger("netsuite-api")

logger.info(
    f"Arranque: MODO_SIMULACION={MODO_SIMULACION} | "
    f"WEBHOOK_SECRET={'configurado' if WEBHOOK_SECRET else 'vacío (no se exige)'}"
)

# =========================
# App
# =========================

app = FastAPI(
    title="NetSuite Integration API",
    version="1.0"
)

# =========================
# Routers
# =========================

app.include_router(netsuite_webhooks.router)

# =========================
# Health check
# =========================

@app.get("/")
def root():
    return {"status": "ok"}


# Endpoint de salud para Coolify (servidor local). Se mantiene "/" igual
# que en Render.
@app.get("/health")
def health():
    return {"status": "ok"}