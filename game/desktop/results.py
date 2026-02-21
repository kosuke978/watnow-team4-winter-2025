"""
結果 API クライアント

desktop 側から api_server を呼び出して、
- セッション開始
- ステージクリア加算
- セッション終了（サーバー側計算・保存）
を行う。
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_API_BASE_URL = os.getenv("RESULT_API_BASE_URL", "https://ball-game-api-1081248663051.asia-northeast1.run.app")
DEFAULT_API_TIMEOUT_SEC = float(os.getenv("RESULT_API_TIMEOUT_SEC", "20"))


class ResultApiError(Exception):
	"""結果 API 呼び出し失敗時の例外。"""


@dataclass
class ResultApiClient:
	base_url: str = DEFAULT_API_BASE_URL
	timeout_sec: float = DEFAULT_API_TIMEOUT_SEC

	def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
		url = f"{self.base_url.rstrip('/')}{path}"
		data = None
		headers = {"Accept": "application/json"}

		if body is not None:
			data = json.dumps(body).encode("utf-8")
			headers["Content-Type"] = "application/json"

		req = urllib.request.Request(url=url, data=data, method=method, headers=headers)

		try:
			with urllib.request.urlopen(req, timeout=self.timeout_sec) as res:
				raw = res.read().decode("utf-8")
				return json.loads(raw) if raw else None
		except urllib.error.HTTPError as e:
			detail = e.read().decode("utf-8", errors="ignore")
			raise ResultApiError(f"{method} {path} failed: {e.code} {detail}") from e
		except urllib.error.URLError as e:
			raise ResultApiError(f"{method} {path} failed: {e.reason}") from e
		except TimeoutError as e:
			raise ResultApiError(f"{method} {path} failed: timeout ({self.timeout_sec}s)") from e
		except socket.timeout as e:
			raise ResultApiError(f"{method} {path} failed: timeout ({self.timeout_sec}s)") from e

	def health(self) -> dict[str, Any]:
		return self._request("GET", "/health")

	def start_session(self, name: str) -> dict[str, Any]:
		return self._request("POST", "/sessions/start", {"name": name})

	def stage_clear(self, session_id: str) -> dict[str, Any]:
		return self._request("POST", f"/sessions/{session_id}/stage-clear", {})

	def finish_session(self, session_id: str) -> dict[str, Any]:
		return self._request("POST", f"/sessions/{session_id}/finish", {})

	def list_results(self, limit: int = 10) -> list[dict[str, Any]]:
		return self._request("GET", f"/results?limit={int(limit)}")


class ResultSessionManager:
	"""ゲームイベントと結果 API を繋ぐ薄いラッパー。"""

	def __init__(self, client: ResultApiClient | None = None):
		self.client = client or ResultApiClient()
		self.session_id: str | None = None
		self.cleared_stages: int = 0

	def on_game_start(self, player_name: str) -> str:
		response = self.client.start_session(player_name)
		self.session_id = str(response["session_id"])
		self.cleared_stages = 0
		return self.session_id

	def on_stage_cleared(self) -> dict[str, Any] | None:
		if not self.session_id:
			return None
		response = self.client.stage_clear(self.session_id)
		self.cleared_stages = int(response.get("cleared_stages", self.cleared_stages + 1))
		return response

	def on_game_finish(self) -> dict[str, Any] | None:
		if not self.session_id:
			return None
		response = self.client.finish_session(self.session_id)
		self.session_id = None
		self.cleared_stages = 0
		return response

	def on_game_abort(self) -> None:
		"""途中終了時にローカルのセッション状態を破棄する。"""
		self.session_id = None
		self.cleared_stages = 0
