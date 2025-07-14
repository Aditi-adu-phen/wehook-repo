from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
print("MongoDB Connected:", client)
db = client["webhook_db"]
collection = db["events"]
collection.insert_one({"message": "👋 Sample GitHub Event Logged"})


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event")

    author = data.get("sender", {}).get("login")
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    if event_type == "push":
        branch = data.get("ref").split("/")[-1]
        message = f'{author} pushed to {branch} on {timestamp}'
    elif event_type == "pull_request":
        from_branch = data.get("pull_request", {}).get("head", {}).get("ref")
        to_branch = data.get("pull_request", {}).get("base", {}).get("ref")
        message = f'{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}'
    else:
        return jsonify({"message": "Unhandled event"}), 200

    collection.insert_one({"message": message})
    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    try:
        events = list(collection.find().sort("_id", -1).limit(10))
        print("Fetched Events from MongoDB:", events)
        messages = []

        for e in events:
            msg = e.get("message", "⚠️ No message field in this event")
            messages.append(msg)

        return jsonify(messages)

    except Exception as e:
        print("🔥 ERROR in /events route:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)
    
    
