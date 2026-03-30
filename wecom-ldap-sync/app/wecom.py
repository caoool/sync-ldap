"""WeCom (WeChat Work) API client.

Uses a self-built app (自建应用) secret with contacts read permission
to access the full department/user APIs.
"""
import logging
import time
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class WeComClient:
    def __init__(self):
        self._token: str | None = None
        self._token_expires_at: float = 0

    @property
    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        resp = requests.get(
            f"{settings.wecom_api_base}/gettoken",
            params={
                "corpid": settings.wecom_corpid,
                "corpsecret": settings.wecom_corpsecret,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom gettoken failed: {data}")
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300
        logger.info("Obtained new WeCom access token")
        return self._token

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        params = params or {}
        params["access_token"] = self._access_token
        resp = requests.get(
            f"{settings.wecom_api_base}{path}",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom API error on {path}: {data}")
        return data

    # ── Departments ─────────────────────────────────────────────────

    def get_departments(self) -> list[dict]:
        """Fetch the full department tree.
        Returns list of dicts with keys: id, name, parentid, order.
        """
        data = self._get("/department/list")
        departments = data.get("department", [])
        logger.info("Fetched %d departments from WeCom", len(departments))
        return departments

    # ── Users ───────────────────────────────────────────────────────

    def get_department_users(self, department_id: int) -> list[dict]:
        """Fetch detailed user list for a department.
        Returns list of user dicts with keys like:
        userid, name, department, position, mobile, email, gender, status, etc.
        """
        data = self._get("/user/list", {"department_id": department_id})
        return data.get("userlist", [])

    def get_all_users(self) -> list[dict]:
        """Fetch all users across all departments.
        Deduplicates users who belong to multiple departments.
        """
        departments = self.get_departments()
        seen: set[str] = set()
        users: list[dict] = []
        for dept in departments:
            dept_users = self.get_department_users(dept["id"])
            for u in dept_users:
                uid = u["userid"]
                if uid not in seen:
                    seen.add(uid)
                    users.append(u)
        logger.info("Fetched %d unique users from WeCom", len(users))
        return users
