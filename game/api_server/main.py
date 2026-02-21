"""
結果保存 API サーバー

保存項目:
- 名前（スマホ入力）
- クリアしたステージ数
- プレイ日時（日本時間）
- クリアにかかった時間（秒）
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from supabase import Client, create_client


JST = ZoneInfo("Asia/Tokyo")
TABLE_NAME = "results"
SESSION_TABLE_NAME = "game_sessions"


load_dotenv()


def get_supabase_client() -> Client:
	url = os.getenv("SUPABASE_URL", "").strip()
	# 互換: SUPABASE_KEY も許可
	key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()

	if not url or not key:
		raise HTTPException(
			status_code=500,
			detail="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) are required",
		)

	return create_client(url, key)


def to_jst(dt: datetime) -> datetime:
	if dt.tzinfo is None:
		return dt.replace(tzinfo=JST)
	return dt.astimezone(JST)


@asynccontextmanager
async def lifespan(_: FastAPI):
	# 起動時に設定チェック
	_ = get_supabase_client()
	yield


app = FastAPI(title="Ball Game Result API", lifespan=lifespan)


class ResultCreate(BaseModel):
	name: str = Field(..., min_length=1, max_length=100)
	cleared_stages: int = Field(..., ge=0)
	clear_seconds: float = Field(..., ge=0)
	# 未指定ならサーバー受信時刻を使う
	played_at: datetime | None = None


class ResultOut(BaseModel):
	id: int
	name: str
	cleared_stages: int
	clear_seconds: float
	played_at_jst: str
	created_at_jst: str


class SessionStartCreate(BaseModel):
	name: str = Field(..., min_length=1, max_length=100)
	started_at: datetime | None = None


class SessionStartOut(BaseModel):
	session_id: str
	name: str
	started_at_jst: str
	cleared_stages: int
	status: str


class SessionProgressOut(BaseModel):
	session_id: str
	cleared_stages: int
	status: str


class SessionFinishCreate(BaseModel):
	finished_at: datetime | None = None


def _row_get_str(row: dict, *keys: str) -> str:
	for key in keys:
		value = row.get(key)
		if value is not None:
			return str(value)
	raise HTTPException(status_code=500, detail=f"missing required field: {', '.join(keys)}")


def _to_jst_iso(value: str) -> str:
	s = str(value).replace("Z", "+00:00")
	dt = datetime.fromisoformat(s)
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=JST)
	else:
		dt = dt.astimezone(JST)
	return dt.isoformat()


def _parse_iso(value: str) -> datetime:
	s = str(value).replace("Z", "+00:00")
	return datetime.fromisoformat(s)


def _to_result_out(row: dict) -> ResultOut:
	played_at = _row_get_str(row, "played_at_jst", "played_at")
	created_at = _row_get_str(row, "created_at_jst", "created_at")

	return ResultOut(
		id=int(row["id"]),
		name=str(row["name"]),
		cleared_stages=int(row["cleared_stages"]),
		clear_seconds=float(row["clear_seconds"]),
		played_at_jst=_to_jst_iso(played_at),
		created_at_jst=_to_jst_iso(created_at),
	)


def _insert_result(
	supabase: Client,
	name: str,
	cleared_stages: int,
	clear_seconds: float,
	played_at_jst: datetime,
	created_at_jst: datetime,
) -> dict:
	primary_payload = {
		"name": name,
		"cleared_stages": cleared_stages,
		"clear_seconds": clear_seconds,
		"played_at": played_at_jst.isoformat(),
		"created_at": created_at_jst.isoformat(),
	}

	try:
		resp = supabase.table(TABLE_NAME).insert(primary_payload).execute()
	except Exception:
		legacy_payload = {
			"name": name,
			"cleared_stages": cleared_stages,
			"clear_seconds": clear_seconds,
			"played_at_jst": played_at_jst.isoformat(),
			"created_at_jst": created_at_jst.isoformat(),
		}
		resp = supabase.table(TABLE_NAME).insert(legacy_payload).execute()

	rows = resp.data or []
	if not rows:
		raise HTTPException(status_code=500, detail="failed to insert result")
	return rows[0]


def _get_session_or_404(supabase: Client, session_id: str) -> dict:
	resp = (
		supabase.table(SESSION_TABLE_NAME)
		.select("*")
		.eq("session_id", session_id)
		.limit(1)
		.execute()
	)
	rows = resp.data or []
	if not rows:
		raise HTTPException(status_code=404, detail="session not found")
	return rows[0]


@app.get("/health")
async def health() -> dict:
	_ = get_supabase_client()
	return {"status": "ok", "storage": "supabase"}


@app.post("/results", response_model=ResultOut)
async def save_result(payload: ResultCreate) -> ResultOut:
	name = payload.name.strip()
	if not name:
		raise HTTPException(status_code=422, detail="name must not be empty")

	now_jst = datetime.now(JST)
	played_at_jst = to_jst(payload.played_at) if payload.played_at else now_jst
	supabase = get_supabase_client()
	inserted = _insert_result(
		supabase=supabase,
		name=name,
		cleared_stages=payload.cleared_stages,
		clear_seconds=payload.clear_seconds,
		played_at_jst=played_at_jst,
		created_at_jst=now_jst,
	)

	return _to_result_out(inserted)


@app.get("/results", response_model=list[ResultOut])
async def list_results(limit: int = 50) -> list[ResultOut]:
	safe_limit = max(1, min(limit, 200))
	supabase = get_supabase_client()
	resp = supabase.table(TABLE_NAME).select("*").order("id", desc=True).limit(safe_limit).execute()
	rows = resp.data or []

	return [
		_to_result_out(row)
		for row in rows
	]


@app.post("/sessions/start", response_model=SessionStartOut)
async def start_session(payload: SessionStartCreate) -> SessionStartOut:
	name = payload.name.strip()
	if not name:
		raise HTTPException(status_code=422, detail="name must not be empty")

	session_id = str(uuid4())
	started_at_jst = to_jst(payload.started_at) if payload.started_at else datetime.now(JST)
	supabase = get_supabase_client()

	resp = supabase.table(SESSION_TABLE_NAME).insert(
		{
			"session_id": session_id,
			"name": name,
			"started_at": started_at_jst.isoformat(),
			"cleared_stages": 0,
			"status": "playing",
		}
	).execute()

	rows = resp.data or []
	if not rows:
		raise HTTPException(status_code=500, detail="failed to start session")

	row = rows[0]
	return SessionStartOut(
		session_id=str(row["session_id"]),
		name=str(row["name"]),
		started_at_jst=_to_jst_iso(_row_get_str(row, "started_at")),
		cleared_stages=int(row.get("cleared_stages", 0)),
		status=str(row.get("status", "playing")),
	)


@app.post("/sessions/{session_id}/stage-clear", response_model=SessionProgressOut)
async def session_stage_clear(session_id: str) -> SessionProgressOut:
	supabase = get_supabase_client()
	session = _get_session_or_404(supabase, session_id)

	if str(session.get("status", "playing")) != "playing":
		raise HTTPException(status_code=409, detail="session already finished")

	next_count = int(session.get("cleared_stages", 0)) + 1
	resp = (
		supabase.table(SESSION_TABLE_NAME)
		.update({"cleared_stages": next_count})
		.eq("session_id", session_id)
		.execute()
	)
	rows = resp.data or []
	if not rows:
		raise HTTPException(status_code=500, detail="failed to update session")

	return SessionProgressOut(session_id=session_id, cleared_stages=next_count, status="playing")


@app.post("/sessions/{session_id}/finish", response_model=ResultOut)
async def finish_session(session_id: str, payload: SessionFinishCreate) -> ResultOut:
	supabase = get_supabase_client()
	session = _get_session_or_404(supabase, session_id)

	if str(session.get("status", "playing")) != "playing":
		raise HTTPException(status_code=409, detail="session already finished")

	started_at_raw = _row_get_str(session, "started_at")
	started_at_jst = to_jst(_parse_iso(started_at_raw))
	finished_at_jst = to_jst(payload.finished_at) if payload.finished_at else datetime.now(JST)

	clear_seconds = max(0.0, (finished_at_jst - started_at_jst).total_seconds())
	cleared_stages = int(session.get("cleared_stages", 0))
	name = str(session.get("name", "")).strip()
	if not name:
		raise HTTPException(status_code=500, detail="session name is empty")

	inserted = _insert_result(
		supabase=supabase,
		name=name,
		cleared_stages=cleared_stages,
		clear_seconds=clear_seconds,
		played_at_jst=started_at_jst,
		created_at_jst=finished_at_jst,
	)

	_ = (
		supabase.table(SESSION_TABLE_NAME)
		.update(
			{
				"finished_at": finished_at_jst.isoformat(),
				"clear_seconds": clear_seconds,
				"status": "finished",
			}
		)
		.eq("session_id", session_id)
		.execute()
	)

	return _to_result_out(inserted)
