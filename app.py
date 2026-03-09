from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "aceest-fitness"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)