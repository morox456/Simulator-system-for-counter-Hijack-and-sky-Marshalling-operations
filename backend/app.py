
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import initialize_database, save_result, get_all_results

app = Flask(__name__)
CORS(app)

# Initialize the database when the service starts.
try:
    initialize_database()
    app.logger.info("Training database initialized.")
except Exception:
    app.logger.exception("Database initialization failed.")


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
        "version": "1.1"
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}

    trainee = str(data.get("trainee") or "Guest").strip()
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
        "4": "report",
        "5": "report"
    }

    scenario_key = str(scenario).strip()
    decision = str(decision).strip().lower()

    if scenario_key not in correct_decisions:
        return jsonify({"error": "Unknown scenario"}), 400

    try:
        response_time = float(response_time)
        if not 0 <= response_time <= 30:
            raise ValueError("Response time must be between 0 and 30 seconds.")
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid response_time"}), 400

    correct_action = correct_decisions[scenario_key]
    is_correct = decision == correct_action

    result = "Correct" if is_correct else "Needs Improvement"
    score = 10 if is_correct else 0

    feedback_messages = {
        "1": "Observe and assess the unusual behavior before deciding on further action.",
        "2": "Communicate the passenger's report to the crew for further assessment.",
        "3": "Observe the situation carefully and avoid making assumptions based only on nervous behavior.",
        "4": "Communicate with the crew to support coordinated assessment.",
        "5": "Report unauthorized entry into a restricted area to the appropriate crew member."
    }

    if decision == "timeout":
        result = "Needs Improvement"
        score = 0
        feedback = (
            "Time expired. Review the scenario and try to make your "
            "decision within the allowed time."
        )
    elif is_correct:
        feedback = "Correct response. " + feedback_messages[scenario_key]
    else:
        feedback = (
            "Review the scenario. " + feedback_messages[scenario_key]
        )

    try:
        save_result(
            trainee,
            scenario_key,
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
        "scenario": scenario_key,
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
