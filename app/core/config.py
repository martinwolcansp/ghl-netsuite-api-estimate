# app/core/config.py

import os

# ==============================
# GHL CORE
# ==============================
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")

# Opcional (solo si escalás pipelines)
GHL_PIPELINE_ID = os.getenv("GHL_PIPELINE_ID")

GHL_BASE_URL = "https://services.leadconnectorhq.com"

# ==============================
# INTEGRACIÓN
# ==============================
CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID = os.getenv(
    "CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID"
)

# ==============================
# VALIDACIONES
# ==============================
if not GHL_API_KEY:
    raise EnvironmentError("Missing GHL_API_KEY")

if not GHL_LOCATION_ID:
    raise EnvironmentError("Missing GHL_LOCATION_ID")

if not CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID:
    raise EnvironmentError("Missing CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID")