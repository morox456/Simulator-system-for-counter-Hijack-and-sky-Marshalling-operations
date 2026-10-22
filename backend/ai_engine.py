
SCENARIO_RULES = {
    "1": {
        "topic": "situational awareness",
        "expected": "observe",
        "difficulty": "Easy",
    },
    "2": {
        "topic": "communication",
        "expected": "report",
        "difficulty": "Easy",
    },
    "3": {
        "topic": "situational awareness",
        "expected": "observe",
        "difficulty": "Medium",
    },
    "4": {
        "topic": "crew coordination",
        "expected": "report",
        "difficulty": "Medium",
    },
    "5": {
        "topic": "restricted-area awareness",
        "expected": "report",
        "difficulty": "Hard",
    },
}


def _get_score(correct, response_time=0):
    """Return a score from 0 to 10."""
    if not correct:
        return 0

    try:
        seconds = max(0, float(response_time))
    except (TypeError, ValueError):
        seconds = 0

    if seconds <= 5:
        return 10
    if seconds <= 10:
        return 9
    if seconds <= 20:
        return 8
    return 7


def _is_correct(expected, decision):
    """Compare normalized decision labels."""
    return str(expected).strip().lower() == str(decision).strip().lower()


def evaluate_decision(scenario, decision, response_time=0):
    """Evaluate one simulated training decision."""
    scenario_id = str(scenario)
    rule = SCENARIO_RULES.get(scenario_id)

    if not rule:
        return {
            "valid": False,
            "error": "Unknown scenario ID.",
        }

    correct = _is_correct(rule["expected"], decision)
    score = _get_score(correct, response_time)

    if correct:
        feedback = "Correct decision. Review the scenario explanation to reinforce your response."
        improvement_tip = "Maintain consistent decision-making and review the scenario context."
    else:
        feedback = (
            "Incorrect decision for this training scenario. "
            "Review the scenario context and the expected response."
        )
        improvement_tip = (
            "Practice this topic again and review the feedback before your next attempt."
        )

    return {
        "valid": True,
        "correct": correct,
        "result": "Correct" if correct else "Incorrect",
        "score": score,
        "feedback": feedback,
        "improvement_tip": improvement_tip,
        "topic": rule["topic"],
        "difficulty": rule["difficulty"],
        "response_time": response_time,
    }


def _record_is_correct(record):
    """Handle the common result fields returned by the database."""
    result = str(
        record.get("result", record.get("status", ""))
    ).strip().lower()

    if result in ("correct", "success", "true"):
        return True

    if result in ("incorrect", "wrong", "timeout", "false"):
        return False

    value = record.get("correct", False)

    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")

    return value is True


def _record_topic(record):
    """Get the topic stored with an attempt or infer it from its scenario ID."""
    topic = record.get("topic")

    if topic and str(topic).strip():
        return str(topic).strip().lower()

    scenario_id = str(
        record.get("scenario_id", record.get("scenario", ""))
    ).strip()

    if scenario_id.lower().startswith("scenario "):
        scenario_id = scenario_id.split()[-1]

    rule = SCENARIO_RULES.get(scenario_id)

    if rule:
        return rule["topic"]

    return "other"


def _record_score(record):
    """Read a stored score safely."""
    value = record.get("score", 0)

    try:
        return max(0.0, min(10.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _record_response_time(record):
    """Read response time safely."""
    value = record.get(
        "response_time",
        record.get("responseTime", 0),
    )

    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def analyze_performance(results):
    """
    Summarize stored attempts consistently.

    Accuracy is the percentage of correct decisions, not the average score.
    A topic's accuracy uses the same correct/attempt count as the overall
    accuracy calculation.
    """
    records = list(results or [])
    total = len(records)

    if total == 0:
        return {
            "attempts": 0,
            "correct_decisions": 0,
            "incorrect_decisions": 0,
            "accuracy": 0,
            "average_score": 0,
            "average_response_time": 0,
            "weak_areas": [],
            "strengths": [],
            "topic_analysis": {},
            "recommendation": (
                "Complete training scenarios to generate personalized advice."
            ),
        }

    correct_count = sum(
        1 for record in records if _record_is_correct(record)
    )

    incorrect_count = total - correct_count

    average_score = sum(
        _record_score(record) for record in records
    ) / total

    average_response_time = sum(
        _record_response_time(record) for record in records
    ) / total

    accuracy = round((correct_count / total) * 100)

    topic_groups = {}

    for record in records:
        topic = _record_topic(record)

        if topic not in topic_groups:
            topic_groups[topic] = {
                "attempts": 0,
                "correct": 0,
                "total_score": 0.0,
                "total_response_time": 0.0,
            }

        group = topic_groups[topic]
        group["attempts"] += 1
        group["correct"] += int(_record_is_correct(record))
        group["total_score"] += _record_score(record)
        group["total_response_time"] += _record_response_time(record)

    topic_analysis = {}

    for topic, group in topic_groups.items():
        attempts = group["attempts"]
        topic_accuracy = round(
            (group["correct"] / attempts) * 100
        )

        topic_analysis[topic] = {
            "attempts": attempts,
            "correct": group["correct"],
            "incorrect": attempts - group["correct"],
            "accuracy": topic_accuracy,
            "average_score": round(
                group["total_score"] / attempts, 1
            ),
            "average_response_time": round(
                group["total_response_time"] / attempts, 1
            ),
        }

    # Use the same topic_accuracy field for both strengths and weak areas.
    weak_areas = sorted(
        [
            {
                "topic": topic,
                "accuracy": data["accuracy"],
                "attempts": data["attempts"],
            }
            for topic, data in topic_analysis.items()
            if data["accuracy"] < 80
        ],
        key=lambda item: item["accuracy"],
    )

    strengths = sorted(
        [
            {
                "topic": topic,
                "accuracy": data["accuracy"],
                "attempts": data["attempts"],
            }
            for topic, data in topic_analysis.items()
            if data["accuracy"] >= 80
        ],
        key=lambda item: item["accuracy"],
        reverse=True,
    )

    if weak_areas:
        weakest = weak_areas[0]
        recommendation = (
            "Prioritize "
            + weakest["topic"]
            + " practice. Current accuracy is "
            + str(weakest["accuracy"])
            + "% across "
            + str(weakest["attempts"])
            + " attempt(s)."
        )
    elif accuracy >= 80:
        recommendation = (
            "Good performance so far. Maintain consistent decisions "
            "and consider a more challenging practice level."
        )
    else:
        recommendation = (
            "Review recent decisions and practice foundational scenarios."
        )

    return {
        "attempts": total,
        "correct_decisions": correct_count,
        "incorrect_decisions": incorrect_count,
        "accuracy": accuracy,
        "average_score": round(average_score, 1),
        "average_response_time": round(average_response_time, 1),
        "weak_areas": weak_areas,
        "strengths": strengths,
        "topic_analysis": topic_analysis,
        "recommendation": recommendation,
    }


def recommend_difficulty(history):
    """Recommend a practice level based on recent saved results."""
    records = list(history or [])

    if not records:
        return {
            "level": "Easy",
            "difficulty": 1,
            "reason": "Start with foundational scenarios and build consistency.",
            "recent_attempts": 0,
            "average_score": 0,
            "accuracy": 0,
            "average_response_time": 0,
        }

    recent = records[:5]

    correct_count = sum(
        1 for record in recent if _record_is_correct(record)
    )

    accuracy = round((correct_count / len(recent)) * 100)

    average_score = sum(
        _record_score(record) for record in recent
    ) / len(recent)

    average_response_time = sum(
        _record_response_time(record) for record in recent
    ) / len(recent)

    if len(recent) >= 3 and average_score >= 8 and accuracy >= 80:
        level = "Hard"
        number = 3
        reason = (
            "Recent results show strong scores and accuracy. "
            "Try the most challenging available practice level."
        )
    elif average_score >= 6 and accuracy >= 60:
        level = "Medium"
        number = 2
        reason = (
            "Your recent results support a balanced practice level."
        )
    else:
        level = "Easy"
        number = 1
        reason = (
            "Review foundational scenarios and build consistency."
        )

    return {
        "level": level,
        "difficulty": number,
        "reason": reason,
        "recent_attempts": len(recent),
        "average_score": round(average_score, 1),
        "accuracy": accuracy,
        "average_response_time": round(average_response_time, 1),
    }
