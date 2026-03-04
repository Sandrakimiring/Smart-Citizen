"""
Trend computation and aggregation for Nyayo Sentinel.

Computes topic trends, spike detection, and summary statistics
from the signals database.
"""

from datetime import datetime, timedelta
from typing import Optional

from . import database as db
from .models import TopicCount, TopicTrend, CountyTension, KnowledgeGap, SentinelStats


def get_topic_counts(days: Optional[int] = None) -> list[TopicCount]:
    """Get question counts by topic, optionally filtered by time window."""
    rows = db.count_by_topic(days=days)
    return [TopicCount(topic=r["topic"], count=r["count"]) for r in rows]


def get_topic_trends(current_days: int = 1, compare_days: int = 7) -> list[TopicTrend]:
    """
    Compare topic counts between current period and a baseline period to detect spikes.

    Args:
        current_days: The recent window (e.g., 1 = today).
        compare_days: The baseline window to compare against (e.g., 7 = last week).

    Returns:
        List of TopicTrend with change percentages and direction.
    """
    current = {r["topic"]: r["count"] for r in db.count_by_topic(days=current_days)}
    baseline = {r["topic"]: r["count"] for r in db.count_by_topic(days=compare_days)}

    trends = []
    # Get all topics seen in either period
    all_topics = set(list(current.keys()) + list(baseline.keys()))

    for topic in all_topics:
        curr = current.get(topic, 0)
        base = baseline.get(topic, 0)

        # Normalize baseline to daily average for fair comparison
        daily_avg = base / compare_days if compare_days > 0 else 0
        # Scale current to same period
        curr_normalized = curr / current_days if current_days > 0 else 0

        if daily_avg > 0:
            change_pct = round(((curr_normalized - daily_avg) / daily_avg) * 100, 1)
        elif curr_normalized > 0:
            change_pct = 100.0  # new topic appearing
        else:
            change_pct = 0.0

        if change_pct > 10:
            direction = "up"
        elif change_pct < -10:
            direction = "down"
        else:
            direction = "stable"

        trends.append(TopicTrend(
            topic=topic,
            current_count=curr,
            previous_count=base,
            change_percent=change_pct,
            direction=direction,
        ))

    # Sort by change_percent descending (biggest spikes first)
    trends.sort(key=lambda t: t.change_percent, reverse=True)
    return trends


def get_county_heatmap(days: Optional[int] = None) -> list[CountyTension]:
    """Get per-county average tension scores for the heatmap."""
    rows = db.county_tension(days=days)
    return [
        CountyTension(
            county=r["county"],
            avg_tension=round(r["avg_tension"], 3),
            question_count=r["question_count"],
        )
        for r in rows
    ]


def get_knowledge_gaps(days: Optional[int] = None) -> KnowledgeGap:
    """Get no-answer rate and sample unanswered questions."""
    data = db.unanswered_questions(days=days)
    return KnowledgeGap(**data)


def get_dashboard_stats(days: Optional[int] = None) -> SentinelStats:
    """Summary statistics for the dashboard header."""
    return SentinelStats(
        total_signals=db.total_signal_count(),
        topics=get_topic_counts(days=days),
        avg_tension=db.avg_tension(days=days),
        counties_covered=db.distinct_counties(),
    )
