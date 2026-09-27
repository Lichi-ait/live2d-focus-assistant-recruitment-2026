"""专注历史的统计与报告函数，保持无框架、易于单独复用。"""
from datetime import datetime
from sqlite3 import Connection
from . import repositories


# 时段边界（小时，左闭右开），与 M02 的时段约定保持一致。
MORNING_START_HOUR = 5
AFTERNOON_START_HOUR = 12
EVENING_START_HOUR = 18


def _ended(connection):
    return [s for s in repositories.all_sessions(connection, include_archived=False) if s["status"] in {"completed", "abandoned"}]


def _start_period(value):
    """按 ISO 开始时间判断所属时段；缺失或无效时返回 None。"""
    try:
        hour = datetime.fromisoformat(value).hour
    except (TypeError, ValueError):
        return None
    if hour < MORNING_START_HOUR:
        return "evening"
    if hour < AFTERNOON_START_HOUR:
        return "morning"
    if hour < EVENING_START_HOUR:
        return "afternoon"
    return "evening"


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

    时段边界（左闭右开，与 M02 的时段约定保持一致）：上午 [05:00, 12:00)、
    下午 [12:00, 18:00)、晚上 [18:00, 24:00) 与 [00:00, 05:00)；三段时间
    覆盖全天且互不重叠，每条有效记录只归入一个时段。

    统计口径：统计所有未归档的会话，不论最终是否完成——本函数关注的是
    何时开始专注，中途放弃的会话同样体现开始习惯。started_at 缺失或无效时
    跳过该条记录，既不影响其它记录，也不会让整个统计崩溃。
    """
    buckets = {"morning": 0, "afternoon": 0, "evening": 0}
    for session in repositories.all_sessions(connection, include_archived=False):
        period = _start_period(session["started_at"])
        if period is not None:
            buckets[period] += 1
    return buckets


def report(connection):
    # Baseline report intentionally exposes only the basic counters. Date-range
    # filtering, streaks and a readable text rendering are left for follow-up work.
    return summary(connection)
