"""Replace the contents of the configured Google Drive weather report."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as HttpRequest, urlopen

from google.auth.transport.requests import Request as AuthRequest
from google.oauth2 import service_account

REPORT = Path("weather-report.md")
FILE_ID = os.environ["GOOGLE_DRIVE_FILE_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"]

if not REPORT.is_file() or not REPORT.read_bytes():
    raise SystemExit("weather-report.md is missing or empty")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_JSON),
    scopes=["https://www.googleapis.com/auth/drive"],
)
credentials.refresh(AuthRequest())

request = HttpRequest(
    f"https://www.googleapis.com/upload/drive/v3/files/{FILE_ID}?uploadType=media&fields=id,name,modifiedTime",
    data=REPORT.read_bytes(),
    headers={
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "text/markdown; charset=utf-8",
    },
    method="PATCH",
)
try:
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
except HTTPError as error:
    details = error.read().decode("utf-8", errors="replace")
    raise SystemExit(f"Drive update failed ({error.code}): {details}") from None

if result.get("id") != FILE_ID:
    raise SystemExit("Drive returned an unexpected file ID")
print("Updated existing Google Drive weather-report.md")
