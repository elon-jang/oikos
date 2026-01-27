"""Google Drive 연동 스크립트 (pull/push/list).

Usage:
    python3 scripts/gdrive.py list              # 폴더 내용 조회
    python3 scripts/gdrive.py pull 0125         # 입력 파일 다운로드
    python3 scripts/gdrive.py push 0125         # 출력 Excel 업로드
"""

import io
import os
import sys
from datetime import datetime

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)
from gdrive_config import (
    ALLOWED_EXTENSIONS,
    GDRIVE_CREDENTIALS_PATH,
    GDRIVE_FOLDER_ID,
    GDRIVE_SCOPES,
    GDRIVE_TOKEN_PATH,
)


def _get_service():
    """Google Drive API 서비스 객체 반환 (인증 포함)."""
    creds = None

    if os.path.exists(GDRIVE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GDRIVE_TOKEN_PATH, GDRIVE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                reason = e.args[0] if e.args else "알 수 없는 원인"
                print(f"토큰 갱신 실패 ({reason}) → 재인증 필요")
                os.remove(GDRIVE_TOKEN_PATH)
                creds = None
        if not creds or not creds.valid:
            if not os.path.exists(GDRIVE_CREDENTIALS_PATH):
                print(f"인증 파일 없음: {GDRIVE_CREDENTIALS_PATH}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                GDRIVE_CREDENTIALS_PATH, GDRIVE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 토큰 저장
        token_dir = os.path.dirname(GDRIVE_TOKEN_PATH)
        os.makedirs(token_dir, exist_ok=True)
        with open(GDRIVE_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def _handle_http_error(e: HttpError, context: str = ""):
    """HttpError를 사용자 친화적 메시지로 변환."""
    status = e.resp.status
    messages = {
        403: "권한 없음 — Drive 폴더 접근 권한을 확인하세요",
        404: "리소스를 찾을 수 없음 — 폴더 ID를 확인하세요",
        429: "API 할당량 초과 — 잠시 후 다시 시도하세요",
    }
    msg = messages.get(status, f"Drive API 오류 (HTTP {status})")
    if context:
        msg = f"{context}: {msg}"
    print(msg)
    sys.exit(1)


def _parse_date(date_str: str) -> tuple[str, str, str]:
    """날짜 문자열 파싱 → (YYYY, MMDD, YYYYMMDD)."""
    if len(date_str) == 4:
        mmdd = date_str
        yyyy = str(datetime.now().year)
    elif len(date_str) == 8:
        yyyy = date_str[:4]
        mmdd = date_str[4:]
    else:
        print(f"날짜 형식 오류: {date_str} (MMDD 또는 YYYYMMDD)")
        sys.exit(1)
    return yyyy, mmdd, f"{yyyy}{mmdd}"


def _find_subfolder(service, parent_id: str, name: str) -> str | None:
    """parent_id 내에서 이름이 name인 폴더 검색."""
    query = (
        f"'{parent_id}' in parents"
        f" and name = '{name}'"
        f" and mimeType = 'application/vnd.google-apps.folder'"
        f" and trashed = false"
    )
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
    except HttpError as e:
        _handle_http_error(e, "폴더 검색")
    files = results.get("files", [])
    return files[0]["id"] if files else None


def _create_subfolder(service, parent_id: str, name: str) -> str:
    """parent_id 내에 이름이 name인 폴더 생성 → 생성된 폴더 ID 반환."""
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    try:
        folder = service.files().create(body=file_metadata, fields="id").execute()
    except HttpError as e:
        _handle_http_error(e, "폴더 생성")
    return folder["id"]


def _list_files(service, folder_id: str, query_extra: str = "") -> list[dict]:
    """폴더 내 파일 목록 조회."""
    query = f"'{folder_id}' in parents and trashed = false"
    if query_extra:
        query += f" and {query_extra}"

    try:
        results = (
            service.files()
            .list(
                q=query,
                fields="files(id, name, size, mimeType, modifiedTime)",
                orderBy="name",
            )
            .execute()
        )
    except HttpError as e:
        _handle_http_error(e, "파일 목록 조회")
    return results.get("files", [])


def cmd_list():
    """루트 폴더 내용 조회."""
    service = _get_service()
    files = _list_files(service, GDRIVE_FOLDER_ID)

    if not files:
        print("폴더가 비어있습니다.")
        return

    print(f"{'이름':<40} {'크기':>10} {'수정일':>12}")
    print("-" * 65)
    for f in files:
        is_folder = f["mimeType"] == "application/vnd.google-apps.folder"
        name = f"[DIR] {f['name']}" if is_folder else f['name']
        size = "-" if is_folder else _format_size(int(f.get("size", 0)))
        modified = f["modifiedTime"][:10]
        print(f"{name:<40} {size:>10} {modified:>12}")


def _format_size(size_bytes: int) -> str:
    """바이트를 읽기 쉬운 형태로 변환."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def cmd_pull(date_str: str):
    """Drive에서 입력 파일 다운로드 → data/YYYY/MMDD/input/."""
    yyyy, mmdd, yyyymmdd = _parse_date(date_str)
    service = _get_service()

    # 출력 디렉토리 생성
    input_dir = os.path.join(BASE_DIR, "data", yyyy, mmdd, "input")
    os.makedirs(input_dir, exist_ok=True)

    files_to_download = []

    # 1) MMDD 하위 폴더 검색
    subfolder_id = _find_subfolder(service, GDRIVE_FOLDER_ID, mmdd)
    if subfolder_id:
        print(f"Drive 폴더 발견: {mmdd}/")
        files_to_download = _list_files(service, subfolder_id)
    else:
        # 2) 루트 폴더에서 파일명에 MMDD 포함된 파일 검색
        print(f"Drive 폴더 '{mmdd}' 없음 → 루트에서 파일명 검색...")
        all_files = _list_files(service, GDRIVE_FOLDER_ID)
        files_to_download = [f for f in all_files if mmdd in f["name"]]

    # 확장자 필터링
    filtered = [
        f
        for f in files_to_download
        if f["mimeType"] != "application/vnd.google-apps.folder"
        and os.path.splitext(f["name"])[1].lower() in ALLOWED_EXTENSIONS
    ]

    if not filtered:
        print(f"다운로드할 파일이 없습니다 (MMDD={mmdd}).")
        return

    # 다운로드
    downloaded = 0
    for f in filtered:
        dest_path = os.path.join(input_dir, f["name"])
        print(f"  다운로드: {f['name']}...", end=" ")

        try:
            request = service.files().get_media(fileId=f["id"])
            with open(dest_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            print("완료")
            downloaded += 1
        except HttpError as e:
            print(f"실패 (HTTP {e.resp.status})")
            continue

    print(f"\n{downloaded}개 파일 → {input_dir}")


def cmd_push(date_str: str):
    """출력 Excel을 Drive에 업로드."""
    yyyy, mmdd, yyyymmdd = _parse_date(date_str)
    service = _get_service()

    xlsx_path = os.path.join(BASE_DIR, "data", yyyy, mmdd, f"{yyyymmdd}.xlsx")
    if not os.path.exists(xlsx_path):
        print(f"파일 없음: {xlsx_path}")
        sys.exit(1)

    filename = os.path.basename(xlsx_path)
    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # 업로드 대상 폴더 결정 (없으면 자동 생성)
    subfolder_id = _find_subfolder(service, GDRIVE_FOLDER_ID, mmdd)
    if subfolder_id:
        target_folder_id = subfolder_id
        print(f"Drive 폴더 발견: {mmdd}/")
    else:
        target_folder_id = _create_subfolder(service, GDRIVE_FOLDER_ID, mmdd)
        print(f"Drive 폴더 생성: {mmdd}/")

    # 기존 파일 확인 (동일 이름 → update)
    existing = _list_files(
        service, target_folder_id, f"name = '{filename}'"
    )

    media = MediaFileUpload(xlsx_path, mimetype=mime_type)

    try:
        if existing:
            # 덮어쓰기
            file_id = existing[0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"업데이트 완료: {filename} (기존 파일 덮어쓰기)")
        else:
            # 신규 업로드
            file_metadata = {"name": filename, "parents": [target_folder_id]}
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            print(f"업로드 완료: {filename} → Drive")
    except HttpError as e:
        _handle_http_error(e, "파일 업로드")


MEMBERS_FILE = os.path.join(SCRIPT_DIR, "members.txt")
MEMBERS_DRIVE_NAME = "members.txt"


def cmd_members_push():
    """교인 명부를 Drive 루트 폴더에 업로드."""
    if not os.path.exists(MEMBERS_FILE):
        print(f"파일 없음: {MEMBERS_FILE}")
        sys.exit(1)

    service = _get_service()
    media = MediaFileUpload(MEMBERS_FILE, mimetype="text/plain")

    existing = _list_files(service, GDRIVE_FOLDER_ID, f"name = '{MEMBERS_DRIVE_NAME}'")

    try:
        if existing:
            file_id = existing[0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"명부 업데이트 완료: {MEMBERS_DRIVE_NAME} (기존 파일 덮어쓰기)")
        else:
            file_metadata = {"name": MEMBERS_DRIVE_NAME, "parents": [GDRIVE_FOLDER_ID]}
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            print(f"명부 업로드 완료: {MEMBERS_DRIVE_NAME} → Drive")
    except HttpError as e:
        _handle_http_error(e, "명부 업로드")


def cmd_members_pull():
    """Drive에서 교인 명부 다운로드."""
    service = _get_service()
    existing = _list_files(service, GDRIVE_FOLDER_ID, f"name = '{MEMBERS_DRIVE_NAME}'")

    if not existing:
        print(f"Drive에 명부 파일 없음: {MEMBERS_DRIVE_NAME}")
        sys.exit(1)

    file_id = existing[0]["id"]
    try:
        request = service.files().get_media(fileId=file_id)
        with open(MEMBERS_FILE, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        print(f"명부 다운로드 완료: {MEMBERS_DRIVE_NAME} → {MEMBERS_FILE}")
    except HttpError as e:
        _handle_http_error(e, "명부 다운로드")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/gdrive.py <command> [date]")
        print("Commands: list, pull <MMDD>, push <MMDD>, members-push, members-pull")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        cmd_list()
    elif command in ("pull", "push"):
        if len(sys.argv) < 3:
            print(f"Usage: python3 scripts/gdrive.py {command} <MMDD>")
            sys.exit(1)
        date_str = sys.argv[2]
        if command == "pull":
            cmd_pull(date_str)
        else:
            cmd_push(date_str)
    elif command == "members-push":
        cmd_members_push()
    elif command == "members-pull":
        cmd_members_pull()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
