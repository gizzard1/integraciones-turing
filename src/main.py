import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRETS_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"
SPREADSHEET_ID = "10ZfvXX1rNpZU9vubjpQDHrXrj0QR00dqvBFHHGSYfXo"
RANGE_LECTURA = "Hoja 1!A2:D100"
RANGE_RESULTADO = "Hoja 1!G2"
COLUMNA_SUBTOTAL = 3
COLUMNA_PZS = 2

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def main():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets().values()

    # 1. LEER
    result = sheet.get(spreadsheetId=SPREADSHEET_ID, range=RANGE_LECTURA).execute()
    rows = result.get("values", [])
    if not rows:
        print("El rango está vacío, no hay nada que calcular.")
        return
    print(f"Leídas {len(rows)} filas.")

    # 2. CALCULAR — sumar la columna indicada
    total = 0.0
    for row in rows:
        try:
            total += float(row[COLUMNA_SUBTOTAL]) * float(row[COLUMNA_PZS])
        except (IndexError, ValueError):
            continue
    print(f"Total: {total}")

    # 3. ACTUALIZAR
    sheet.update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_RESULTADO,
        valueInputOption="USER_ENTERED",
        body={"values": [[total]]},
    ).execute()
    print(f"Registro actualizado en {RANGE_RESULTADO}")


if __name__ == "__main__":
    main()