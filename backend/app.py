
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import initialize_database, save_result, get_all_results
from ai_engine import (
    evaluate_decision,
    recommend_difficulty,
    analyze_performance,
)

app = Flask(__name__)
CORS(app)

initialize_database()


# Keep these topic mappings consistent with backend/ai_engine.py.
SCENARIO_TOPICS = {
    "1": "situational awareness",
    "2": "communication",
    "3": "situational awareness",
    "4": "crew coordination",
    "5": "restricted-area awareness",
}

AVAILABLE_SCENARIOS = list(SCENARIO_TOPICS.keys())


def filter_trainee_records(records, trainee):
    """Filter records by trainee name without case sensitivity."""
    if not trainee:
        return list(records)

    target = trainee.strip().casefold()

    return [
        record
        for record in records
        if str(record.get("trainee", "")).strip().casefold() == target
    ]


def get_scenario_id(record):
    """Normalize scenario IDs returned by the database."""
    value = record.get("scenario_id", record.get("scenario", ""))

    scenario = str(value).strip()

    if scenario.lower().startswith("scenario "):
        scenario = scenario.split()[-1]

    return scenario


def choose_next_scenario(records):
    """
    Choose a scenario using the trainee's saved performance.

    Priority:
    1. Practise a topic with accuracy below 80%.
    2. Within that topic, prefer the least-practised scenario.
    3. If no weak topic exists, balance practice across topics.
    4. Avoid repeating the most recent scenario when alternatives exist.
    """
    records = list(records or [])

    if not records:
        return {
            "scenario": "1",
            "topic": SCENARIO_TOPICS["1"],
            "reason": (
                "No previous attempts were found. Start with a "
                "foundational situational-awareness scenario."
            ),
        }

    analysis = analyze_performance(records)
    topic_analysis = analysis.get("topic_analysis", {}) or {}

    scenario_counts = {
        scenario: 0 for scenario in AVAILABLE_SCENARIOS
    }

    topic_counts = {
        topic: 0 for topic in set(SCENARIO_TOPICS.values())
    }

    latest_scenario = get_scenario_id(records[0])

    for record in records:
        scenario = get_scenario_id(record)

        if scenario in scenario_counts:
            scenario_counts[scenario] += 1

        topic = SCENARIO_TOPICS.get(scenario)

        if topic:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Find the weakest topic using the accuracy calculated by the engine.
    weak_topics = []

    for topic, details in topic_analysis.items():
        try:
            accuracy = float(details.get("accuracy", 0))
            attempts = int(details.get("attempts", 0))
        except (TypeError, ValueError):
            continue

        if attempts > 0 and accuracy < 80:
            weak_topics.append({
                "topic": topic.strip().lower(),
                "accuracy": accuracy,
                "attempts": attempts,
            })

    if weak_topics:
        weak_topics.sort(
            key=lambda item: (
                item["accuracy"],
                -item["attempts"],
            )
        )

        target_topic = weak_topics[0]["topic"]
        accuracy = weak_topics[0]["accuracy"]

        reason = (
            f"Extra practice is recommended for {target_topic}, "
            f"which currently has {accuracy:.0f}% accuracy."
        )
    else:
        # No weak topic: practise the least-practised topic.
        target_topic = min(
            topic_counts,
            key=lambda topic: topic_counts[topic],
        )

        reason = (
            f"No topic below 80% accuracy was identified. "
            f"This scenario helps maintain balanced practice in "
            f"{target_topic}."
        )

    candidates = [
        scenario
        for scenario, topic in SCENARIO_TOPICS.items()
        if topic == target_topic
    ]

    # If an older engine or database uses an unrecognized topic,
    # fall back to all supported scenarios.
    if not candidates:
        candidates = AVAILABLE_SCENARIOS
        target_topic = None

    # Prefer scenarios attempted fewer times.
    least_attempted = min(scenario_counts[item] for item in candidates)

    candidates = [
        item
        for item in candidates
        if scenario_counts[item] == least_attempted
    ]

    # Avoid an immediate repeat if another equally suitable option exists.
    if len(candidates) > 1 and latest_scenario in candidates:
        candidates.remove(latest_scenario)

    # Deterministic tie-breaker for predictable behaviour.
    selected = sorted(candidates)[0]
    selected_topic = SCENARIO_TOPICS[selected]

    return {
        "scenario": selected,
        "topic": selected_topic,
        "reason": reason,
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Sky Marshal Simulator Backend is running",
        "ai_engine": "enabled",
        "engine_type": "Rule-based adaptive evaluation",
        "version": "2.3",
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "project": (
            "Virtual Simulator for Counter-Hijacking and "
            "Sky Marshalling Operations"
        ),
        "status": "Backend is working",
        "ai_engine": "enabled",
        "engine_type": "Rule-based adaptive evaluation",
        "features": [
            "Scenario decision evaluation",
            "Personalized decision feedback",
            "Performance analysis",
            "Topic-based strengths and weaknesses",
            "Response-time analysis",
            "Adaptive difficulty recommendations",
            "Adaptive next-scenario selection",
            "Persistent training history",
        ],
        "version": "2.3",
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}

    trainee = str(data.get("trainee") or "Guest").strip()[:100]
    scenario = data.get("scenario")
    decision = str(data.get("decision") or "").strip().lower()

    if scenario is None or not decision:
        return jsonify({
            "error": "scenario and decision are required"
        }), 400

    try:
        response_time = float(data.get("response_time", 0))

        if response_time < 0:
            raise ValueError

    except (TypeError, ValueError):
        return jsonify({
            "error": "response_time must be a non-negative number"
        }), 400

    evaluation = evaluate_decision(
        scenario,
        decision,
        response_time,
    )

    if not evaluation.get("valid"):
        return jsonify({
            "error": "Unknown scenario"
        }), 400

    try:
        save_result(
            trainee,
            str(scenario),
            decision,
            evaluation["result"],
            evaluation["score"],
            response_time,
        )

    except Exception:
        app.logger.exception("Could not save training result")

        return jsonify({
            "error": "Could not save training result"
        }), 500

    return jsonify({
        "status": "success",
        "trainee": trainee,
        "scenario": str(scenario),
        "decision": decision,
        "response_time": response_time,
        "result": evaluation["result"],
        "correct": evaluation.get(
            "correct",
            evaluation["result"] == "Correct",
        ),
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "improvement_tip": evaluation.get(
            "improvement_tip",
            evaluation["feedback"],
        ),
        "topic": evaluation["topic"],
        "difficulty": evaluation["difficulty"],
    })


@app.route("/api/results", methods=["GET"])
def results():
    try:
        records = get_all_results()
        return jsonify(records)

    except Exception:
        app.logger.exception("Could not retrieve training results")

        return jsonify({
            "error": "Could not retrieve results"
        }), 500


@app.route("/api/analysis", methods=["GET"])
def analysis():
    trainee = request.args.get("trainee", "").strip()

    try:
        records = get_all_results()
        records = filter_trainee_records(records, trainee)

        summary = analyze_performance(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "analysis": summary,
        })

    except Exception:
        app.logger.exception("Performance analysis failed")

        return jsonify({
            "error": "Could not analyze performance"
        }), 500


@app.route("/api/difficulty", methods=["GET"])
@app.route("/api/adaptive-difficulty", methods=["GET"])
@app.route("/api/recommend-difficulty", methods=["GET"])
def difficulty():
    trainee = request.args.get("trainee", "").strip()

    try:
        records = get_all_results()
        records = filter_trainee_records(records, trainee)

        recommendation = recommend_difficulty(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "recommendation": recommendation,
            # Compatibility fields for existing frontend code.
            "difficulty": recommendation["level"],
            "level": recommendation["level"],
            "reason": recommendation["reason"],
        })

    except Exception:
        app.logger.exception("Difficulty recommendation failed")

        return jsonify({
            "error": "Could not recommend difficulty"
        }), 500


@app.route("/api/next-scenario", methods=["GET"])
def next_scenario():
    trainee = request.args.get("trainee", "").strip()

    try:
        all_records = get_all_results()
        records = filter_trainee_records(all_records, trainee)

        selection = choose_next_scenario(records)
        difficulty_recommendation = recommend_difficulty(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "scenario": selection["scenario"],
            "topic": selection["topic"],
            "reason": selection["reason"],
            "difficulty": difficulty_recommendation["level"],
            "difficulty_number": difficulty_recommendation["difficulty"],
            "difficulty_reason": difficulty_recommendation["reason"],
            "based_on_attempts": len(records),
        })

    except Exception:
        app.logger.exception("Adaptive scenario selection failed")

        return jsonify({
            "error": "Could not select the next scenario"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
