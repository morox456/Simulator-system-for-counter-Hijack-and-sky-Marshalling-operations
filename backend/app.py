
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import initialize_database, save_result, get_all_results

app = Flask(__name__)
CORS(app)

initialize_database()


@app.route("/")
def home():
    return jsonify({"message": "Sky Marshal Simulator Backend is running"})


@app.route("/api/status")
def status():
    return jsonify({
        "project": "Virtual Simulator for Counter-Hijacking and Sky Marshalling Operations",
        "status": "Backend is working",
        "version": "1.0"
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}

    trainee = str(data.get("trainee", "Guest")).strip() or "Guest"
    scenario = str(data.get("scenario", ""))
    decision = str(data.get("decision", "")).strip().lower()

    try:
        response_time = max(0, float(data.get("response_time", 0)))
    except (TypeError, ValueError):
        response_time = 0

    if not scenario or not decision:
        return jsonify({
            "error": "Scenario and decision are required"
        }), 400

    correct = decision == scenario.strip().lower()
    result = "Correct" if correct else "Incorrect"
    score = 10 if correct else 0

    feedback = (
        "Good decision. The selected response is appropriate "
        "for the simulated situation."
        if correct else
        "Review the scenario and choose the response that best "
        "matches the training guidance."
    )

    try:
        save_result(
            trainee, scenario, decision, result,
            score, response_time
        )
    except Exception:
        app.logger.exception("Could not save trainee result")
        return jsonify({"error": "Could not save training result"}), 500

    return jsonify({
        "result": result,
        "score": score,
        "feedback": feedback,
        "response_time": response_time
    })


@app.route("/api/results", methods=["GET"])
def results():
    try:
        return jsonify(get_all_results())
    except Exception:
        app.logger.exception("Could not retrieve results")
        return jsonify({"error": "Could not retrieve results"}), 500


if __name__ == "__main__":
    app.run(debug=True)
