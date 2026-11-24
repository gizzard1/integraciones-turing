"""
Automatización diaria v2: avisar por Gmail cuando cambia el total
acumulado.

Cómo funciona:
  - Lee la hoja y suma la columna de ventas (columna D) por la columna de piezas (columna C).
  - Las ventas no avisadas son las que tienen la columna
    "Venta notificada" (columna E) vacía o en "No".
  - Si hay ventas no avisadas, las manda en UN solo correo con el
    total anterior y el total actual, y luego marca esas filas
    como "Sí" en la columna E, directo en el Sheet.

  El total anterior se guarda en una celda fija del mismo Sheet:
    Hoja 1!G2 = último total avisado (se crea si no existe).

  Si es la primera corrida, solo guarda el total actual como base
  y NO manda correo por las ventas viejas.

Autenticación: mismo OAuth Client ID de la integración anterior.

APIs a habilitar:
    gcloud services enable sheets.googleapis.com gmail.googleapis.com
"""

import base64
from email.message import EmailMessage
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
COLUMNA_NOTIFICADA = 4
CELDA_TOTAL_ANTERIOR = "Hoja 1!H2"
DESTINATARIO = "admin@agenda-master.com.mx"


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_creds():
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
    return creds

def enviar_correo(gmail, destinatario, asunto, cuerpo):
    msg = EmailMessage()
    msg["To"] = destinatario
    msg["From"] = "me"
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"Correo enviado a {destinatario}: {asunto}")


def main():
    creds = get_creds()

    sheets = build("sheets", "v4", credentials=creds)
    gmail = build("gmail", "v1", credentials=creds)
    values = sheets.spreadsheets().values()

    # 1. LEER
    result = values.get(spreadsheetId=SPREADSHEET_ID, range=RANGE_LECTURA).execute()
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

    # 3. Leer el total anterior guardado en el Sheet
    try:
        prev = values.get(
            spreadsheetId=SPREADSHEET_ID, range=CELDA_TOTAL_ANTERIOR
        ).execute()
        prev_values = prev.get("values", [])
        last_total = float(prev_values[0][0]) if prev_values else None
    except (ValueError, IndexError):
        last_total = None

    
    # Primera corrida: guardar el total como base, sin mandar correo
    if last_total is None:
        values.update(
            spreadsheetId=SPREADSHEET_ID,
            range=CELDA_TOTAL_ANTERIOR,
            valueInputOption="USER_ENTERED",
            body={"values": [[total]]},
        ).execute()
        print(f"Primera revisión. Total actual: {total}. Base guardada, sin correo.")
        return

    # 4. Ventas no notificadas: columna E vacía o "No"
    pendientes = []
    for i, row in enumerate(rows):
        notificada = ""
        if len(row) > COLUMNA_NOTIFICADA:
            notificada = row[COLUMNA_NOTIFICADA].strip().lower()
        if notificada not in ("sí", "si", "yes", "x"):
            pendientes.append((i + 2, row))  # +2: fila real (encabezado + índice)

    if total == last_total or not pendientes:
        print(f"Sin cambios. Total sigue en {total}. Nada por avisar.")
        return


    # 5. Mandar UN correo con todas las ventas no vistas
    lineas = "\n".join(f"- Fila {n}: {row[COLUMNA_PZS]} unidades de ${row[COLUMNA_SUBTOTAL]}" for n, row in pendientes)
    cuerpo = (
        "Cambió el total acumulado de ventas.\n\n"
        f"Total anterior: {last_total}\n"
        f"Total actual: {total}\n"
        f"Diferencia: {total - last_total}\n\n"
        "Ventas no notificadas:\n"
        f"{lineas}"
    )
    enviar_correo(
        gmail,
        DESTINATARIO,
        f"Total de ventas cambió: {last_total} → {total}",
        cuerpo,
    )


    # 6. Marcar esas filas como notificadas en la columna E
    data = [
        {
            "range": f"Hoja 1!E{n}",
            "values": [["Sí"]],
        }
        for n, _ in pendientes
    ]
    values.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()

    # 7. Actualizar el total guardado
    values.update(
        spreadsheetId=SPREADSHEET_ID,
        range=CELDA_TOTAL_ANTERIOR,
        valueInputOption="USER_ENTERED",
        body={"values": [[total]]},
    ).execute()
    print(f"{len(pendientes)} venta(s) marcadas como notificadas.")


if __name__ == "__main__":
    main()