#!/usr/bin/env python3
"""
Einmaliges Setup-Script: Microsoft Graph Refresh Token holen.

Schritte:
  1. Python-Abhängigkeit installieren: pip install msal
  2. Dieses Script ausführen: python get_ms_token.py
  3. Dem Link folgen, mit deinem Microsoft-Account anmelden
  4. Den angezeigten REFRESH_TOKEN als GitHub Secret speichern

Azure App Registration (einmalig unter https://portal.azure.com):
  - "App registrations" → "New registration"
  - Name: z.B. "IQAM Dashboard"
  - Account types: "Accounts in this organizational directory only"
  - Redirect URI: "Public client/native" → http://localhost
  - Nach Erstellung: "API permissions" → "Add permission" → "Microsoft Graph"
    → Delegated → "Mail.Read" → "Add permissions"
  - Unter "Authentication": "Allow public client flows" → YES aktivieren
  - CLIENT_ID und TENANT_ID aus der App-Übersicht kopieren
"""

import json

# ─── HIER AUSFÜLLEN ──────────────────────────────────────────────────────────
CLIENT_ID = "DEINE_CLIENT_ID_HIER"   # z.B. "12345678-abcd-..."
TENANT_ID = "DEINE_TENANT_ID_HIER"  # z.B. "87654321-dcba-..." oder "sunrisesecurities.com"
# ─────────────────────────────────────────────────────────────────────────────

SCOPES = ["https://graph.microsoft.com/Mail.Read", "offline_access"]

try:
    import msal
except ImportError:
    print("❌ MSAL nicht installiert. Bitte ausführen:")
    print("   pip install msal")
    exit(1)

app = msal.PublicClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
)

# Device code flow – kein Browser öffnen nötig, Link + Code wird angezeigt
flow = app.initiate_device_flow(scopes=SCOPES)
if "user_code" not in flow:
    print(f"❌ Fehler: {flow}")
    exit(1)

print("\n" + "="*60)
print("🔐 Microsoft Login erforderlich")
print("="*60)
print(f"\n1. Öffne: {flow['verification_uri']}")
print(f"2. Gib diesen Code ein: {flow['user_code']}")
print("\nWarte auf Anmeldung...")
print("="*60 + "\n")

result = app.acquire_token_by_device_flow(flow)

if "error" in result:
    print(f"❌ Fehler: {result['error_description']}")
    exit(1)

refresh_token = result.get("refresh_token", "")
access_token  = result.get("access_token", "")

print("\n✅ Erfolgreich authentifiziert!\n")
print("─"*60)
print("GitHub Secrets (unter Settings → Secrets → Actions speichern):")
print("─"*60)
print(f"\nMS_CLIENT_ID:\n  {CLIENT_ID}")
print(f"\nMS_TENANT_ID:\n  {TENANT_ID}")
print(f"\nMS_REFRESH_TOKEN:\n  {refresh_token}")
print("\n─"*60)
print("⚠️  Den Refresh Token NICHT teilen oder committen!")
print("─"*60)

# Optionaler Test
print("\n📧 Teste E-Mail-Zugriff...")
from urllib.request import Request, urlopen
req = Request(
    "https://graph.microsoft.com/v1.0/me/messages?$top=1&$filter=from/emailAddress/address eq 'rbi-fondsreporting@rbinternational.com'&$select=subject,receivedDateTime",
    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
)
try:
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("value"):
        msg = data["value"][0]
        print(f"  ✅ Letzter Fund-Report: {msg['subject']}")
        print(f"     Empfangen: {msg['receivedDateTime'][:10]}")
    else:
        print("  ⚠️  Keine Mails von rbi-fondsreporting gefunden.")
except Exception as e:
    print(f"  ❌ Test fehlgeschlagen: {e}")
