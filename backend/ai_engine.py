
"""AI evaluation and adaptive difficulty for the Sky Marshal Simulator."""

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
    """Evaluate a trainee decision using transparent scenario rules."""
    scenario_id = str(scenario)
    action = str(decision or "").strip().lower()
    rule = SCENARIO_RULES.get(scenario_id)

    if rule is None:
        return {
            "valid": False,
            "result": "Invalid scenario",
            "score": 0,
            "feedback": "This scenario is not configured for evaluation.",
            "topic": "unknown",
            "difficulty": 1,
        }

    if action == "timeout":
        return {
            "valid": True,
            "result": "Needs Improvement",
            "score": 0,
            "feedback": (
                "Time expired. Review the scenario and respond within "
                "the time limit. Follow approved training procedures."
            ),
            "topic": rule["topic"],
            "difficulty": rule["difficulty"],
        }

    correct = action == rule["expected"]

    if correct:
        feedback = (
            f"Correct decision. You demonstrated appropriate "
            f"{rule['topic']}. Continue following approved procedures "
            f"and coordinating with the cabin crew."
        )
        score = 10
        result = "Correct"
    else:
        expected = rule["expected"]
        if expected == "observe":
            guidance = (
                "Observe and assess the situation carefully. Unusual "
                "behavior alone does not establish wrongdoing."
            )
        else:
            guidance = (
                "Communicate the concern to the appropriate cabin crew "
                "member and follow established procedures."
            )

        feedback = (
            f"Needs improvement in {rule['topic']}. {guidance}"
        )
        score = 0
        result = "Needs Improvement"

    return {
        "valid": True,
        "result": result,
        "score": score,
        "feedback": feedback,
        "topic": rule["topic"],
        "difficulty": rule["difficulty"],
    }


def recommend_difficulty(history):
    """Recommend training difficulty from recent evaluation history.

    History items should contain a score from 0 to 10.
    This is a rule-based adaptation, not a trained ML model.
    """
    recent = list(history)[-5:]

    if not recent:
        return {
            "level": "Easy",
            "difficulty": 1,
            "reason": "Start with introductory scenarios.",
        }

    scores = []
    for item in recent:
        try:
            scores.append(
                max(0, min(10, float(item.get("score", 0))))
            )
        except (TypeError, ValueError):
            scores.append(0)

    average = sum(scores) / len(scores)

    if len(scores) >= 3 and average >= 8:
        return {
            "level": "Hard",
            "difficulty": 3,
            "reason": (
                "Recent results are consistently strong. "
                "Introduce more challenging practice scenarios."
            ),
        }

    if average >= 6:
        return {
            "level": "Medium",
            "difficulty": 2,
            "reason": (
                "Continue practicing with moderate complexity "
                "to reinforce consistent decisions."
            ),
        }

    return {
        "level": "Easy",
        "difficulty": 1,
        "reason": (
            "Reinforce the fundamentals before increasing "
            "scenario complexity."
        ),
    }


def analyze_performance(results):
    """Summarize accuracy and identify topics for more practice."""
    results = list(results)

    if not results:
        return {
            "attempts": 0,
            "accuracy": 0,
            "average_score": 0,
            "areas_to_improve": [],
            "recommendation": "Complete a scenario to begin analysis.",
        }

    correct = sum(
        1 for item in results
        if str(item.get("result", "")).lower() == "correct"
    )
    scores = []

    for item in results:
        try:
            scores.append(float(item.get("score", 0)))
        except (TypeError, ValueError):
            scores.append(0)

    topic_attempts = defaultdict(int)
    topic_errors = defaultdict(int)

    for item in results:
        evaluation = evaluate_decision(
            item.get("scenario"),
            item.get("decision"),
            item.get("response_time", 0),
        )
        topic = evaluation.get("topic", "unknown")
        topic_attempts[topic] += 1

        if evaluation.get("result") != "Correct":
            topic_errors[topic] += 1

    weak_topics = [
        topic for topic, attempts in topic_attempts.items()
        if attempts and topic_errors[topic] / attempts >= 0.5
    ]

    accuracy = round(correct / len(results) * 100)
    average_score = round(sum(scores) / len(scores), 2)

    if weak_topics:
        recommendation = (
            "Prioritize practice in: " + ", ".join(weak_topics) + "."
        )
    elif accuracy >= 80:
        recommendation = (
            "Good performance. Progress to more challenging "
            "practice scenarios when appropriate."
        )
    else:
        recommendation = (
            "Review the feedback from incorrect answers and "
            "repeat foundational scenarios."
        )

    return {
        "attempts": len(results),
        "accuracy": accuracy,
        "average_score": average_score,
        "areas_to_improve": weak_topics,
        "recommendation": recommendation,
    }
