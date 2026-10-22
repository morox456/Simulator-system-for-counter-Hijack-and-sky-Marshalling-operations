
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import initialize_database, save_result, get_all_results
from ai_engine import (
    evaluate_decision,
    recommend_difficulty,
    analyze_performance,
    choose_next_scenario,
)

app = Flask(__name__)
CORS(app)

initialize_database()


def filter_trainee_records(records, trainee):
    """Filter records by trainee name without case sensitivity."""
    if not trainee:
        return list(records)

    target = trainee.strip().casefold()

    return [
        record for record in records
        if str(record.get("trainee", "")).strip().casefold() == target
    ]


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Sky Marshal Simulator Backend is running",
        "ai_engine": "enabled",
        "engine_type": "Rule-based adaptive evaluation",
        "version": "2.4",
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
        "version": "2.4",
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
        "correct": evaluation["correct"],
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "improvement_tip": evaluation["improvement_tip"],
        "topic": evaluation["topic"],
        "difficulty": evaluation["difficulty"],
    })


@app.route("/api/results", methods=["GET"])
def results():
    try:
        return jsonify(get_all_results())
    except Exception:
        app.logger.exception("Could not retrieve training results")
        return jsonify({
            "error": "Could not retrieve results"
        }), 500


@app.route("/api/analysis", methods=["GET"])
def analysis():
    trainee = request.args.get("trainee", "").strip()

    try:
        records = filter_trainee_records(get_all_results(), trainee)
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
        records = filter_trainee_records(get_all_results(), trainee)
        recommendation = recommend_difficulty(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "recommendation": recommendation,
            # Compatibility fields for the existing frontend.
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
        records = filter_trainee_records(get_all_results(), trainee)

        selection = choose_next_scenario(records)
        difficulty = recommend_difficulty(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "scenario": selection["scenario"],
            "topic": selection["topic"],
            "reason": selection["reason"],
            "based_on_attempts": selection["based_on_attempts"],
            "difficulty": difficulty["level"],
            "difficulty_number": difficulty["difficulty"],
            "difficulty_reason": difficulty["reason"],
        })
    except Exception:
        app.logger.exception("Adaptive scenario selection failed")
        return jsonify({
            "error": "Could not select the next scenario"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
