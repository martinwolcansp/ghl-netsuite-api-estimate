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

# ==============================
# MIGRACIÓN AL SERVIDOR LOCAL (Parte II)
# ==============================
# Interruptores para la réplica en el servidor local. Apagados por
# defecto: sin estas variables el servicio se comporta igual que en Render.

# MODO_SIMULACION=true -> hace las lecturas reales (búsqueda en GHL) pero
# no el PUT: registra en el log, con el prefijo [SIMULACION], lo que
# habría enviado.
MODO_SIMULACION = os.getenv("MODO_SIMULACION", "false").strip().lower() in (
    "true", "1", "si", "sí", "yes"
)

# WEBHOOK_SECRET con valor -> exige el header X-Integration-Secret (o el
# parámetro ?token=) en cada webhook y rechaza con 401 lo que no lo traiga.
# Vacío -> no exige nada.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()