
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import save_result, get_all_results

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Sky Marshal Simulator Backend is running"
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "project": "Virtual Simulator for Counter-Hijacking and Sky Marshalling Operations",
        "status": "Backend is working",
        "version": "1.0"
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}

    trainee = data.get("trainee", "Guest")
    scenario = data.get("scenario")
    decision = data.get("decision")
    response_time = data.get("response_time", 0)

    if scenario is None or decision is None:
        return jsonify({
            "error": "scenario and decision are required"
        }), 400

    correct_decisions = {
        "1": "observe",
        "2": "report",
        "3": "observe",
        "4": "report"
    }

    scenario_key = str(scenario)
    decision = str(decision).strip().lower()
    correct_action = correct_decisions.get(scenario_key)

    if correct_action is None:
        return jsonify({"error": "Unknown scenario"}), 400

    is_correct = decision == correct_action

    result = "Correct" if is_correct else "Needs Improvement"
    score = 10 if is_correct else 0

    feedback = (
        "Good decision for this simulated scenario."
        if is_correct
        else "Review the scenario and try to choose the expected response."
    )

    try:
        save_result(
            trainee,
            scenario,
            decision,
            result,
            score,
            response_time
        )
    except Exception:
        app.logger.exception("Could not save training result")
        return jsonify({
            "error": "Could not save training result"
        }), 500

    return jsonify({
        "trainee": trainee,
        "scenario": scenario,
        "decision": decision,
        "response_time": response_time,
        "result": result,
        "score": score,
        "feedback": feedback
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
