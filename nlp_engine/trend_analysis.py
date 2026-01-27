from collections import defaultdict
from datetime import datetime
from typing import List, Dict


def analyze_topic_trends(
    topics: List[int],
    timestamps: List[datetime]
) -> Dict[int, float]:
    topic_time_count = defaultdict(lambda: defaultdict(int))

    for topic, ts in zip(topics, timestamps):
        week_key = ts.strftime("%Y-%W")
        topic_time_count[topic][week_key] += 1

    trend_scores = {}

    for topic, weeks in topic_time_count.items():
        counts = list(weeks.values())

        if len(counts) < 2:
            continue

        growth_rate = (counts[-1] - counts[0]) / max(1, counts[0])
        trend_scores[topic] = round(growth_rate, 3)

    return trend_scores


# 🔥 Alias expected by run_pipeline
def analyze_trends(topics, timestamps):
    return analyze_topic_trends(topics, timestamps)
