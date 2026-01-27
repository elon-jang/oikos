"""Google Drive API 설정."""

import os

# Google Drive 폴더 ID (헌금 전표 폴더)
GDRIVE_FOLDER_ID = os.environ.get(
    "GDRIVE_FOLDER_ID", "1AoSihy8FvbqrQP6Jzfjuw1cnKIBSoqx4"
)

# OAuth 인증 파일 경로
GDRIVE_CREDENTIALS_PATH = os.path.expanduser(
    os.environ.get(
        "GDRIVE_CREDENTIALS_PATH", "~/elon/credentials/gdrive-credentials.json"
    )
)

# 토큰 캐시 파일 경로
GDRIVE_TOKEN_PATH = os.path.expanduser(
    os.environ.get("GDRIVE_TOKEN_PATH", "~/elon/credentials/gdrive-token.json")
)

# API 스코프
GDRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]

# 다운로드 허용 확장자
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
