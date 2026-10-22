
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
    return str(expected).strip().lower() == str(decision).strip().lower()


def evaluate_decision(scenario, decision, response_time=0):
    """Evaluate a simulated training decision."""
    scenario_id = str(scenario).strip()
    rule = SCENARIO_RULES.get(scenario_id)

    if not rule:
        return {"valid": False, "error": "Unknown scenario ID."}

    correct = _is_correct(rule["expected"], decision)
    score = _get_score(correct, response_time)

    if correct:
        feedback = (
            "Correct decision. Review the scenario explanation "
            "to reinforce your response."
        )
        improvement_tip = (
            "Maintain consistent decision-making and review "
            "the scenario context."
        )
    else:
        feedback = (
            "Incorrect decision for this training scenario. "
            "Review the scenario context and expected response."
        )
        improvement_tip = (
            "Practise this topic again and review the feedback "
            "before your next attempt."
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
    """Read correctness consistently from stored database records."""
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


def _record_scenario(record):
    """Normalize scenario IDs such as 'Scenario 3' to '3'."""
    value = record.get("scenario_id", record.get("scenario", ""))
    scenario_id = str(value).strip()

    if scenario_id.lower().startswith("scenario "):
        scenario_id = scenario_id.split()[-1]

    return scenario_id


def _record_topic(record):
    """Read a saved topic or infer it from the scenario ID."""
    topic = record.get("topic")

    if topic and str(topic).strip():
        return str(topic).strip().lower()

    rule = SCENARIO_RULES.get(_record_scenario(record))
    return rule["topic"] if rule else "other"


def _record_score(record):
    try:
        return max(0.0, min(10.0, float(record.get("score", 0))))
    except (TypeError, ValueError):
        return 0.0


def _record_response_time(record):
    value = record.get("response_time", record.get("responseTime", 0))

    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def analyze_performance(results):
    """Calculate overall and topic-specific training statistics."""
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

    correct_count = sum(_record_is_correct(r) for r in records)
    incorrect_count = total - correct_count

    average_score = sum(_record_score(r) for r in records) / total
    average_time = sum(_record_response_time(r) for r in records) / total
    accuracy = round(correct_count / total * 100)

    groups = {}

    for record in records:
        topic = _record_topic(record)

        if topic not in groups:
            groups[topic] = {
                "attempts": 0,
                "correct": 0,
                "score_total": 0.0,
                "time_total": 0.0,
            }

        group = groups[topic]
        group["attempts"] += 1
        group["correct"] += int(_record_is_correct(record))
        group["score_total"] += _record_score(record)
        group["time_total"] += _record_response_time(record)

    topic_analysis = {}

    for topic, group in groups.items():
        attempts = group["attempts"]

        topic_analysis[topic] = {
            "attempts": attempts,
            "correct": group["correct"],
            "incorrect": attempts - group["correct"],
            "accuracy": round(group["correct"] / attempts * 100),
            "average_score": round(group["score_total"] / attempts, 1),
            "average_response_time": round(group["time_total"] / attempts, 1),
        }

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
        key=lambda item: (item["accuracy"], -item["attempts"]),
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
            f"Prioritize {weakest['topic']} practice. Current accuracy is "
            f"{weakest['accuracy']}% across {weakest['attempts']} attempt(s)."
        )
    elif accuracy >= 80:
        recommendation = (
            "Good performance so far. Maintain consistent decisions "
            "and consider a more challenging practice level."
        )
    else:
        recommendation = (
            "Review recent decisions and practise foundational scenarios."
        )

    return {
        "attempts": total,
        "correct_decisions": correct_count,
        "incorrect_decisions": incorrect_count,
        "accuracy": accuracy,
        "average_score": round(average_score, 1),
        "average_response_time": round(average_time, 1),
        "weak_areas": weak_areas,
        "strengths": strengths,
        "topic_analysis": topic_analysis,
        "recommendation": recommendation,
    }


def recommend_difficulty(history):
    """Recommend difficulty from the trainee's five most recent attempts."""
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
    count = len(recent)
    accuracy = round(
        sum(_record_is_correct(r) for r in recent) / count * 100
    )
    average_score = sum(_record_score(r) for r in recent) / count
    average_time = sum(_record_response_time(r) for r in recent) / count

    if count >= 3 and average_score >= 8 and accuracy >= 80:
        level, number = "Hard", 3
        reason = (
            "Recent results show strong scores and accuracy. "
            "Try the most challenging available practice level."
        )
    elif average_score >= 6 and accuracy >= 60:
        level, number = "Medium", 2
        reason = "Your recent results support a balanced practice level."
    else:
        level, number = "Easy", 1
        reason = "Review foundational scenarios and build consistency."

    return {
        "level": level,
        "difficulty": number,
        "reason": reason,
        "recent_attempts": count,
        "average_score": round(average_score, 1),
        "accuracy": accuracy,
        "average_response_time": round(average_time, 1),
    }


def choose_next_scenario(history):
    """
    Adapt scenario selection to the trainee's saved results.

    Weak topics are prioritized first. Within a topic, choose the
    least-practised available scenario and avoid immediate repetition
    where another suitable scenario exists.
    """
    records = list(history or [])
    available = list(SCENARIO_RULES.keys())

    scenario_counts = {scenario_id: 0 for scenario_id in available}
    topic_counts = {}
    latest_scenario = _record_scenario(records[0]) if records else None

    for record in records:
        scenario_id = _record_scenario(record)

        if scenario_id in scenario_counts:
            scenario_counts[scenario_id] += 1

        topic = _record_topic(record)
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    if not records:
        return {
            "scenario": "1",
            "topic": SCENARIO_RULES["1"]["topic"],
            "reason": (
                "No previous attempts were found. Start with a "
                "foundational situational-awareness scenario."
            ),
            "based_on_attempts": 0,
        }

    analysis = analyze_performance(records)
    topic_analysis = analysis["topic_analysis"]

    weak_topics = [
        (topic, details)
        for topic, details in topic_analysis.items()
        if details["accuracy"] < 80
    ]

    if weak_topics:
        # Lowest accuracy wins; if tied, prefer the topic with more attempts.
        weak_topics.sort(
            key=lambda item: (
                item[1]["accuracy"],
                -item[1]["attempts"],
                item[0],
            )
        )
        target_topic, details = weak_topics[0]
        reason = (
            f"Extra practice is recommended for {target_topic}, "
            f"which currently has {details['accuracy']}% accuracy."
        )
    else:
        # Practise the least-covered topic to keep training balanced.
        all_topics = sorted({rule["topic"] for rule in SCENARIO_RULES.values()})
        target_topic = min(
            all_topics,
            key=lambda topic: (topic_counts.get(topic, 0), topic),
        )
        reason = (
            f"No topic below 80% accuracy was identified. "
            f"Continue balanced practice in {target_topic}."
        )

    candidates = [
        scenario_id
        for scenario_id, rule in SCENARIO_RULES.items()
        if rule["topic"] == target_topic
    ]

    # Prefer scenarios attempted fewer times.
    minimum_count = min(scenario_counts[item] for item in candidates)
    candidates = [
        item for item in candidates
        if scenario_counts[item] == minimum_count
    ]

    # Avoid repeating the last scenario if a suitable alternative exists.
    if len(candidates) > 1 and latest_scenario in candidates:
        candidates.remove(latest_scenario)

    selected = sorted(candidates)[0]

    return {
        "scenario": selected,
        "topic": SCENARIO_RULES[selected]["topic"],
        "scenario_difficulty": SCENARIO_RULES[selected]["difficulty"],
        "reason": reason,
        "based_on_attempts": len(records),
    }
