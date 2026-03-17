import os
import httpx
from typing import Optional

TOKEN_FILE = "token.txt"

class AuthManager:
    def __init__(self, file_path: str = TOKEN_FILE):
        self.file_path = file_path
        self.login: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session: Optional[str] = None

    def _read_tokens(self) -> bool:
        if not os.path.exists(self.file_path):
            return False
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if len(lines) < 3:
                return False
            self.login = lines[0]
            self.access_token = lines[1]
            self.refresh_token = lines[2]
        return True

    def _save_tokens(self, login: str, access: str, refresh: str):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(f"{login}\n{access}\n{refresh}")

    def _validate_access_token(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            r = httpx.get("https://apiarm.axioma24.ru/auth/login", headers=headers, timeout=10)
            data = r.json()
            if data.get("success"):
                self.session = data["result"]["session"]
                return True
        except Exception as e:
            print("Access token check failed:", e)
        return False

    def _refresh_token(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.refresh_token}"}
            r = httpx.get("https://apiarm.axioma24.ru/auth/refresh", headers=headers, timeout=10)
            data = r.json()
            if data.get("success"):
                new_tokens = data["result"]
                self._save_tokens(self.login, new_tokens["access_token"], new_tokens["refresh_token"])
                return self._read_tokens() and self._validate_access_token()
        except Exception as e:
            print("Refresh token failed:", e)
        return False

    def authorize(self) -> Optional[str]:
        if not self._read_tokens():
            return None
        if self._validate_access_token():
            return self.access_token
        if self._refresh_token():
            return self.access_token
        return None
