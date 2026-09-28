"""专注历史的统计与报告函数，保持无框架、易于单独复用。"""
from datetime import datetime
from sqlite3 import Connection
from . import repositories

def _ended(connection):
    return [s for s in repositories.all_sessions(connection, include_archived=False) if s["status"] in {"completed", "abandoned"}]

def summary(connection):
    rows = _ended(connection)
    completed = [s for s in rows if s["status"] == "completed"]
    durations = [max(0, s["duration_seconds"] - s["remaining_seconds"]) for s in completed]
    return {"total_sessions": len(rows), "completed_sessions": len(completed),
            "abandoned_sessions": len(rows) - len(completed),
            "total_focus_seconds": sum(durations),
            "average_focus_seconds": round(sum(durations) / len(durations), 1) if durations else 0,
            "completion_rate": round(len(completed) / len(rows), 4) if rows else 0}

def daily_summary(connection, days=30):
    """兼容统计接口；按日期的完整聚合留作 M01。"""
    if days <= 0:
        return []
    return []

def time_buckets(connection):
    """兼容统计接口；时段边界与聚合留作 M02。"""
    return {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}

def start_time_buckets(connection):
    """按开始时间统计上午、下午、晚上开始的会话数量。

    边界（左闭右开）：上午 [05:00, 12:00)、下午 [12:00, 18:00)、
    晚上 [18:00, 24:00) 与 [00:00, 05:00)。
    只统计未归档的会话，不看是否完成；started_at 缺失或无效时跳过该条。
    """
    buckets = {"morning": 0, "afternoon": 0, "evening": 0}
    for session in repositories.all_sessions(connection, include_archived=False):
        try:
            hour = datetime.fromisoformat(session["started_at"]).hour
        except (TypeError, ValueError):
            continue
        if 5 <= hour < 12:
            buckets["morning"] += 1
        elif 12 <= hour < 18:
            buckets["afternoon"] += 1
        else:
            buckets["evening"] += 1
    return buckets

def report(connection):
    # Baseline report intentionally exposes only the basic counters. Date-range
    # filtering, streaks and a readable text rendering are left for follow-up work.
    return summary(connection)

