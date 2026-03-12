import os

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")

if not GHL_API_KEY:
    raise EnvironmentError("Falta la variable de entorno GHL_API_KEY")
if not GHL_LOCATION_ID:
    raise EnvironmentError("Falta la variable de entorno GHL_LOCATION_ID")

GHL_BASE_URL = "https://services.leadconnectorhq.com"