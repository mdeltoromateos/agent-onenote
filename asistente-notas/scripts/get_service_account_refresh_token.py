"""Obtiene un refresh_token delegado de Microsoft Graph para una cuenta fija
(svc_servinlabs_01), usando el flujo de device code (sin contraseña en este
script: solo hay que iniciar sesion en el navegador con el codigo mostrado).

Este token se guarda UNA VEZ en Secret Manager y el agente lo usa para
renovar access tokens siempre como la misma cuenta, sin pedir login a cada
usuario de Gemini Enterprise.

Uso:
  uv run python scripts/get_service_account_refresh_token.py

Sigue las instrucciones en pantalla: abre https://microsoft.com/devicelogin,
introduce el codigo, e inicia sesion con svc_servinlabs_01@preservinform.onmicrosoft.com.
"""

from __future__ import annotations

import os
import time

import requests

_TENANT_ID = "c01595bd-a38f-4ffe-b850-67914a7ef848"
_CLIENT_ID = "09b748e7-18b3-4009-9333-b6692f4eb369"
_CLIENT_SECRET = os.environ.get("MS_ENTRA_CLIENT_SECRET")
_SCOPE = "offline_access https://graph.microsoft.com/Notes.Read"

_DEVICE_CODE_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/devicecode"
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"


def main() -> int:
    resp = requests.post(
        _DEVICE_CODE_URL,
        data={"client_id": _CLIENT_ID, "scope": _SCOPE},
        timeout=30,
    )
    resp.raise_for_status()
    device = resp.json()

    print(device["message"])
    print()
    print("Esperando a que inicies sesion...")

    interval = device.get("interval", 5)
    expires_at = time.time() + device.get("expires_in", 900)

    while time.time() < expires_at:
        time.sleep(interval)
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": _CLIENT_ID,
            "device_code": device["device_code"],
        }
        if _CLIENT_SECRET:
            data["client_secret"] = _CLIENT_SECRET
        prepared = requests.Request("POST", _TOKEN_URL, data=data).prepare()
        print("DEBUG body:", repr(prepared.body))
        print("DEBUG headers:", dict(prepared.headers))
        token_resp = requests.post(_TOKEN_URL, data=data, timeout=30)
        payload = token_resp.json()

        if token_resp.status_code == 200:
            print("\nLogin correcto.")
            print("\nrefresh_token (guardalo en Secret Manager, no lo compartas por email/chat sin necesidad):\n")
            print(payload["refresh_token"])
            return 0

        error = payload.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue

        print(f"Error: {payload}")
        return 1

    print("Tiempo de espera agotado sin completar el login.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
