from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return jsonify({
        "message": "Sky Marshal Simulator Backend is running"
    })


@app.route("/api/status")
def status():
    return jsonify({
        "project": "Virtual Simulator for Counter-Hijacking and Sky Marshalling Operations",
        "status": "Backend is working",
        "version": "1.0"
    })


@app.route("/api/evaluate", methods=["POST"])
def evaluate():

    data = request.get_json()

    trainee = data.get("trainee", "Unknown")
    scenario = data.get("scenario", "")
    decision = data.get("decision", "")
    response_time = data.get("response_time", 0)

    # Basic evaluation rules
    correct_decisions = {
        "observe": "observe",
        "report": "report"
    }

    correct_action = correct_decisions.get(scenario)

    if decision == correct_action:

        result = "Correct"
        score = 10

        feedback = (
            "Good decision. The selected response "
            "is appropriate for the simulated situation."
        )

    else:

        result = "Needs Improvement"
        score = 0

        feedback = (
            "The selected response was not the expected "
            "response for this simulated scenario."
        )

    return jsonify({

        "trainee": trainee,
        "scenario": scenario,
        "decision": decision,
        "response_time": response_time,
        "result": result,
        "score": score,
        "feedback": feedback

    })


if __name__ == "__main__":
    app.run(debug=True)