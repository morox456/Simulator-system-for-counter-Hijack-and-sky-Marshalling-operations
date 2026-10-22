
"""AI evaluation and adaptive difficulty for the Sky Marshal Simulator.

Uses transparent, rule-based evaluation and performance analysis.
This is not a trained machine-learning model.
"""

from collections import defaultdict


SCENARIO_RULES = {
    "1": {
        "expected": "observe",
        "topic": "situational awareness",
        "difficulty": 1,
    },
    "2": {
        "expected": "report",
        "topic": "communication",
        "difficulty": 1,
    },
    "3": {
        "expected": "observe",
        "topic": "situational awareness",
        "difficulty": 2,
    },
    "4": {
        "expected": "report",
        "topic": "crew coordination",
        "difficulty": 2,
    },
    "5": {
        "expected": "report",
        "topic": "restricted-area awareness",
        "difficulty": 2,
    },
}


def evaluate_decision(scenario, decision, response_time=0):
    """Evaluate a decision using configured scenario rules."""
    scenario_id = str(scenario)
    action = str(decision or "").strip().lower()
    rule = SCENARIO_RULES.get(scenario_id)

    try:
        elapsed = max(0.0, float(response_time or 0))
    except (TypeError, ValueError):
        elapsed = 0.0

    if rule is None:
        return {
            "valid": False,
            "result": "Invalid scenario",
            "score": 0,
            "correct": False,
            "feedback": "This scenario is not configured for evaluation.",
            "topic": "unknown",
            "difficulty": 1,
            "response_time": elapsed,
            "improvement_tip": "Use a configured training scenario.",
        }

    if action == "timeout":
        return {
            "valid": True,
            "result": "Needs Improvement",
            "score": 0,
            "correct": False,
            "feedback": (
                "Time expired. Review the scenario and respond within "
                "the time limit. Follow approved training procedures."
            ),
            "topic": rule["topic"],
            "difficulty": rule["difficulty"],
            "response_time": elapsed,
            "improvement_tip": (
                "Read the scenario carefully and practice making a "
                "timely decision without skipping required procedures."
            ),
        }

    correct = action == rule["expected"]

    if correct:
        feedback = (
            f"Correct decision. You demonstrated appropriate "
            f"{rule['topic']}. Continue following approved procedures "
            "and coordinating with the cabin crew."
        )
        improvement_tip = (
            "Maintain this approach and continue applying the "
            "approved training procedures consistently."
        )
        score = 10
        result = "Correct"
    else:
        if rule["expected"] == "observe":
            guidance = (
                "Observe and assess the situation carefully. Unusual "
                "behavior alone does not establish wrongdoing."
            )
        else:
            guidance = (
                "Communicate the concern to the appropriate cabin crew "
                "member and follow established procedures."
            )

        feedback = f"Needs improvement in {rule['topic']}. {guidance}"
        improvement_tip = guidance
        score = 0
        result = "Needs Improvement"

    return {
        "valid": True,
        "result": result,
        "score": score,
        "correct": correct,
        "feedback": feedback,
        "topic": rule["topic"],
        "difficulty": rule["difficulty"],
        "response_time": elapsed,
        "improvement_tip": improvement_tip,
    }


def _get_score(item):
    """Read and safely constrain a recorded score."""
    try:
        return max(0.0, min(10.0, float(item.get("score", 0))))
    except (TypeError, ValueError, AttributeError):
        return 0.0


def _is_correct(item):
    """Support both stored result labels and explicit correct flags."""
    result = str(item.get("result", "")).strip().lower()

    if result == "correct":
        return True

    if result in {
        "incorrect",
        "needs improvement",
        "wrong",
        "timeout",
        "invalid scenario",
    }:
        return False

    return item.get("correct") is True


def recommend_difficulty(history):
    """Recommend a level using the trainee's five most recent records."""
    recent = list(history)[-5:]

    if not recent:
        return {
            "level": "Easy",
            "difficulty": 1,
            "reason": "Start with introductory scenarios.",
            "recent_attempts": 0,
            "average_score": 0,
            "accuracy": 0,
        }

    scores = [_get_score(item) for item in recent]
    average = sum(scores) / len(scores)
    accuracy = round(
        sum(1 for item in recent if _is_correct(item))
        / len(recent) * 100
    )

    try:
        average_time = sum(
            max(0.0, float(item.get("response_time", 0) or 0))
            for item in recent
        ) / len(recent)
    except (TypeError, ValueError, AttributeError):
        average_time = 0.0

    # Require both strong results and a minimum number of recent attempts
    # before recommending the most challenging available level.
    if len(recent) >= 3 and average >= 8 and accuracy >= 80:
        level = "Hard"
        difficulty = 3
        reason = (
            "Recent results show strong scores and accuracy. "
            "Try the most challenging available practice level."
        )
    elif average >= 6 and accuracy >= 60:
        level = "Medium"
        difficulty = 2
        reason = (
            "Continue with moderate complexity to build consistent "
            "decision-making performance."
        )
    else:
        level = "Easy"
        difficulty = 1
        reason = (
            "Reinforce the fundamentals before increasing "
            "scenario complexity."
        )

    return {
        "level": level,
        "difficulty": difficulty,
        "reason": reason,
        "recent_attempts": len(recent),
        "average_score": round(average, 2),
        "accuracy": accuracy,
        "average_response_time": round(average_time, 2),
    }


def analyze_performance(results):
    """Summarize performance, weak topics, response time, and next steps."""
    results = list(results)

    if not results:
        return {
            "attempts": 0,
            "accuracy": 0,
            "average_score": 0,
            "average_response_time": 0,
            "areas_to_improve": [],
            "topic_analysis": {},
            "recommendation": "Complete a scenario to begin analysis.",
            "strengths": [],
        }

    correct_count = sum(1 for item in results if _is_correct(item))
    scores = [_get_score(item) for item in results]

    response_times = []
    for item in results:
        try:
            response_times.append(
                max(0.0, float(item.get("response_time", 0) or 0))
            )
        except (TypeError, ValueError, AttributeError):
            response_times.append(0.0)

    topic_attempts = defaultdict(int)
    topic_correct = defaultdict(int)

    for item in results:
        scenario_id = str(item.get("scenario", ""))
        rule = SCENARIO_RULES.get(scenario_id)

        # Use the configured scenario topic when available. This avoids
        # evaluating a historic decision twice just to identify its topic.
        topic = rule["topic"] if rule else "unknown"
        topic_attempts[topic] += 1

        if _is_correct(item):
            topic_correct[topic] += 1

    topic_analysis = {}
    weak_topics = []
    strengths = []

    for topic, attempts in topic_attempts.items():
        topic_accuracy = round(topic_correct[topic] / attempts * 100)
        topic_analysis[topic] = {
            "attempts": attempts,
            "correct": topic_correct[topic],
            "accuracy": topic_accuracy,
        }

        if topic_accuracy < 60:
            weak_topics.append(topic)
        elif topic_accuracy >= 80:
            strengths.append(topic)

    accuracy = round(correct_count / len(results) * 100)
    average_score = round(sum(scores) / len(scores), 2)
    average_time = round(sum(response_times) / len(response_times), 2)

    if weak_topics:
        recommendation = (
            "Prioritize practice in: "
            + ", ".join(sorted(weak_topics))
            + ". Review the feedback for incorrect decisions."
        )
    elif accuracy >= 80:
        recommendation = (
            "Good performance so far. Maintain consistent decisions "
            "and consider a more challenging practice level."
        )
    else:
        recommendation = (
            "Review feedback from incorrect decisions and repeat "
            "foundational scenarios to build consistency."
        )

    return {
        "attempts": len(results),
        "correct_decisions": correct_count,
        "incorrect_decisions": len(results) - correct_count,
        "accuracy": accuracy,
        "average_score": average_score,
        "average_response_time": average_time,
        "areas_to_improve": sorted(weak_topics),
        "strengths": sorted(strengths),
        "topic_analysis": topic_analysis,
        "recommendation": recommendation,
    }
