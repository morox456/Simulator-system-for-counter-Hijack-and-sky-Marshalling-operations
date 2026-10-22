
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import initialize_database, save_result, get_all_results
from ai_engine import evaluate_decision, recommend_difficulty, analyze_performance

app = Flask(__name__)
CORS(app)

initialize_database()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Sky Marshal Simulator Backend is running",
        "ai_engine": "enabled"
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "project": "Virtual Simulator for Counter-Hijacking and Sky Marshalling Operations",
        "status": "Backend is working",
        "ai_engine": "enabled",
        "features": [
            "Decision evaluation",
            "Performance analysis",
            "Adaptive difficulty"
        ],
        "version": "2.1"
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}

    trainee = str(data.get("trainee") or "Guest").strip()[:100]
    scenario = data.get("scenario")
    decision = str(data.get("decision") or "").strip().lower()

    try:
        response_time = max(0, float(data.get("response_time", 0)))
    except (TypeError, ValueError):
        return jsonify({
            "error": "response_time must be a number"
        }), 400

    if scenario is None or not decision:
        return jsonify({
            "error": "scenario and decision are required"
        }), 400

    evaluation = evaluate_decision(scenario, decision, response_time)

    if not evaluation["valid"]:
        return jsonify({"error": "Unknown scenario"}), 400

    try:
        save_result(
            trainee,
            str(scenario),
            decision,
            evaluation["result"],
            evaluation["score"],
            response_time
        )
    except Exception:
        app.logger.exception("Could not save training result")
        return jsonify({
            "error": "Could not save training result"
        }), 500

    return jsonify({
        "trainee": trainee,
        "scenario": str(scenario),
        "decision": decision,
        "response_time": response_time,
        "result": evaluation["result"],
        "score": evaluation["score"],
        "feedback": evaluation["feedback"],
        "topic": evaluation["topic"],
        "difficulty": evaluation["difficulty"]
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
    try:
        records = get_all_results()
        summary = analyze_performance(records)

        return jsonify({
            "status": "success",
            "analysis": summary
        })
    except Exception:
        app.logger.exception("Performance analysis failed")
        return jsonify({
            "error": "Could not analyze performance"
        }), 500


# All three URLs now access the same adaptive-difficulty function.
@app.route("/api/difficulty", methods=["GET"])
@app.route("/api/adaptive-difficulty", methods=["GET"])
@app.route("/api/recommend-difficulty", methods=["GET"])
def difficulty():
    trainee = request.args.get("trainee", "").strip()

    try:
        records = get_all_results()

        if trainee:
            records = [
                record for record in records
                if str(record.get("trainee", "")).lower()
                == trainee.lower()
            ]

        recommendation = recommend_difficulty(records)

        return jsonify({
            "status": "success",
            "trainee": trainee or "all trainees",
            "recommendation": recommendation
        })
    except Exception:
        app.logger.exception("Difficulty recommendation failed")
        return jsonify({
            "error": "Could not recommend difficulty"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
