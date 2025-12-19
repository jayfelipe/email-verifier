from flask import Flask, request, jsonify
from .tasks import verify_email_task
import os
import uuid

app = Flask(__name__)

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json or {}
    email = data.get("email")
    source_ip = request.headers.get("X-Real-IP") or request.remote_addr
    if not email:
        return jsonify({"error": "email missing"}), 400

    job_id = str(uuid.uuid4())
    # Llamada asíncrona
    task = verify_email_task.apply_async(args=[email, source_ip, job_id], task_id=job_id)
    return jsonify({"job_id": job_id, "task_id": task.id}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
