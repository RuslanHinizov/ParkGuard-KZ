"""
ollama_service.py — Gemma 4 AI Asistanı (Ollama API)

Ollama local API üzerinden Gemma4:26b modeline istek gönderir.
Park ihlali verilerini context olarak ekler.
Streaming modda yanıt döner.
"""

import httpx
import json
import logging
import sqlite3
from datetime import datetime

from config import DB_PATH

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma4:latest"


async def is_ollama_available(timeout: float = 3.0) -> bool:
    """Ollama health kontrolu."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return response.status_code == 200
    except Exception:
        return False

SYSTEM_PROMPT = """Ты — виртуальный ассистент системы Korgen Vision.
Korgen Vision — аппаратно-программный комплекс для автоматической фото- и видеофиксации нарушений правил дорожного движения в Республике Казахстан.
Система использует IP-камеры для мониторинга парковок: Камера 1 (Въезд), Камера 2 (Парковка-А), Камера 3 (Парковка-Б).

Ты помогаешь операторам:
- Отвечать на вопросы о нарушениях, номерных знаках, зонах, статистике
- Анализировать данные и выявлять закономерности
- Формировать краткие отчёты по запросу
- Объяснять работу системы

Тебе будут переданы актуальные данные системы в разделе [ДАННЫЕ СИСТЕМЫ].
Отвечай кратко, чётко и по делу. Не упоминай названия сторонних AI-моделей.
Если данных нет — честно скажи об этом.
Отвечай на том языке, на котором написан вопрос (русский, казахский, турецкий или английский)."""


def _get_context_data() -> dict:
    """SQLite'dan bugünün istatistiklerini ve son alarmları çek."""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row

            # Bugünkü özet
            total = conn.execute(
                "SELECT COUNT(*) FROM alarms WHERE created_at >= ?",
                (f"{today}T00:00:00",),
            ).fetchone()[0]

            active = conn.execute(
                "SELECT COUNT(*) FROM alarms WHERE created_at >= ? AND status = 'active'",
                (f"{today}T00:00:00",),
            ).fetchone()[0]

            resolved = conn.execute(
                "SELECT COUNT(*) FROM alarms WHERE created_at >= ? AND status = 'resolved'",
                (f"{today}T00:00:00",),
            ).fetchone()[0]

            # Kamera bazlı bugün
            cam_rows = conn.execute(
                """SELECT camera_id, COUNT(*) as cnt
                   FROM alarms WHERE created_at >= ?
                   GROUP BY camera_id""",
                (f"{today}T00:00:00",),
            ).fetchall()
            by_camera = {f"Камера {r['camera_id']}": r["cnt"] for r in cam_rows}

            # Son 10 alarm
            recent_rows = conn.execute(
                """SELECT plate, camera_id, zone_name, duration_sec, status,
                          strftime('%H:%M', created_at) as time
                   FROM alarms ORDER BY created_at DESC LIMIT 10"""
            ).fetchall()
            recent = [dict(r) for r in recent_rows]

            # En çok ihlal yapan plakalar
            top_rows = conn.execute(
                """SELECT plate, COUNT(*) as count
                   FROM alarms WHERE plate IS NOT NULL
                   GROUP BY plate ORDER BY count DESC LIMIT 5"""
            ).fetchall()
            top = [{"plate": r["plate"], "count": r["count"]} for r in top_rows]

        return {
            "сегодня": {
                "дата": today,
                "всего_нарушений": total,
                "активных": active,
                "закрытых": resolved,
                "по_камерам": by_camera,
            },
            "последние_10_нарушений": recent,
            "топ_5_нарушителей_всё_время": top,
        }
    except Exception as e:
        logger.warning(f"Context verisi alinamadi: {e}")
        return {"ошибка": "База данных недоступна"}


async def stream_chat(messages: list[dict]):
    """
    Ollama API'ye streaming chat isteği gönder.
    AsyncGenerator — frontend'e chunk chunk metin döner.
    """
    context = _get_context_data()
    context_str = json.dumps(context, ensure_ascii=False, indent=2)

    system_with_data = (
        f"{SYSTEM_PROMPT}\n\n"
        f"[ДАННЫЕ СИСТЕМЫ]\n{context_str}"
    )

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_with_data},
            *messages,
        ],
        "stream": True,
        "options": {
            "temperature": 0.7,
            "num_ctx": 4096,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    yield f"[Ошибка Ollama: HTTP {response.status_code}]"
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("done"):
                            break
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    except httpx.ConnectError:
        yield "[Ошибка: Ollama не запущен. Выполните: ollama serve]"
    except httpx.ReadTimeout:
        yield "[Ошибка: Таймаут ответа от Ollama]"
    except Exception as e:
        logger.error(f"Ollama istek hatasi: {e}")
        yield f"[Ошибка: {e}]"


async def generate_daily_report(date: str) -> str | None:
    """
    Belirli bir günün verilerini AI ile analiz et (non-streaming).
    Scheduler tarafından çağrılır.
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute(
                "SELECT COUNT(*) FROM alarms WHERE date(created_at) = ?", (date,)
            ).fetchone()[0]

            if total == 0:
                return f"Дата: {date}\n\nНарушений не зафиксировано."

            active = conn.execute(
                "SELECT COUNT(*) FROM alarms WHERE date(created_at) = ? AND status='active'", (date,)
            ).fetchone()[0]
            resolved = total - active

            cam_rows = conn.execute(
                "SELECT camera_id, COUNT(*) as cnt FROM alarms WHERE date(created_at) = ? GROUP BY camera_id",
                (date,),
            ).fetchall()
            cam_info = ", ".join(f"Камера {r['camera_id']}: {r['cnt']}" for r in cam_rows)

            top_rows = conn.execute(
                """SELECT plate, COUNT(*) as cnt FROM alarms
                   WHERE date(created_at) = ? AND plate IS NOT NULL
                   GROUP BY plate ORDER BY cnt DESC LIMIT 5""",
                (date,),
            ).fetchall()
            top_info = ", ".join(f"{r['plate']}({r['cnt']})" for r in top_rows) or "нет данных"

        data_text = (
            f"Дата: {date}\n"
            f"Всего нарушений: {total}\n"
            f"Активных: {active}, Закрытых: {resolved}\n"
            f"По камерам: {cam_info}\n"
            f"Топ нарушители: {top_info}"
        )

        prompt = (
            f"Составь краткий ежедневный отчёт для системы мониторинга парковок Korgen Vision.\n\n"
            f"Данные за {date}:\n{data_text}\n\n"
            f"Отчёт должен содержать: краткую сводку, выводы, рекомендации."
        )

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "Ты — аналитик системы Korgen Vision. Пиши кратко и профессионально."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.5, "num_ctx": 4096},
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")

        return None
    except Exception as e:
        logger.error(f"Daily report olusturma hatasi: {e}")
        return None
