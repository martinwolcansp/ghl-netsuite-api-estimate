from fastapi import FastAPI
import logging

from app.routers import netsuite_webhooks

# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger("netsuite-api")

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