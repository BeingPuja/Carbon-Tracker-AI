from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


# New imports for NLP Chatbot
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import os


# Import your custom modules
from backend.models import create_user, find_user, add_or_update_entry, get_entries, get_entries_since_date
from backend.calculator import total_emission


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_FOLDER = os.path.join(BASE_DIR, "frontend")


app = Flask(__name__, static_folder=FRONTEND_FOLDER)
CORS(app)
app.config["JWT_SECRET_KEY"] = "change-me"
jwt = JWTManager(app)


# ------------------ NLP Chatbot ------------------
try:
    print("Loading conversational model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
   
    # Using the smaller, more efficient model
    model_name = "microsoft/DialoGPT-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
   
    chatbot_pipeline = pipeline("conversational", model=model, tokenizer=tokenizer, device=device)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    chatbot_pipeline = None


def get_carbon_context(user_id):
    """Fetches recent user data to provide context to the AI."""
    recent_entries = get_entries_since_date(user_id, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    if not recent_entries:
        return "The user has not logged any data yet."
   
    df = pd.DataFrame(recent_entries)
    avg_transport = round(df['transport_em'].mean(), 2)
    avg_energy = round(df['energy_em'].mean(), 2)
    avg_diet = round(df['diet_em'].mean(), 2)
   
    context = f"The user's average daily emissions for the past week are: {avg_transport} kg CO2 from transport, {avg_energy} kg CO2 from energy, and {avg_diet} kg CO2 from diet."


    is_plant_based_day = any(e.get("diet") in ["vegetarian", "vegan"] for e in recent_entries)
    if is_plant_based_day:
        context += " The user has recently logged a vegetarian or vegan meal."


    return context


@app.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    if not chatbot_pipeline:
        return jsonify({"response": "The chatbot model could not be loaded. Please check the server logs."}), 500
       
    username = get_jwt_identity()
    user = find_user(username)
    data = request.get_json() or {}
    user_message = data.get("message", "")


    if not user_message:
        return jsonify({"response": "Say something!"})


    # --- New Logic for handling "tips" ---
    tips_keywords = ["tips", "advice", "help", "suggestion"]
    if any(keyword in user_message.lower() for keyword in tips_keywords):
        predefined_tips = (
            "Here are some tips to reduce your carbon footprint:\n\n"
            "1. Reduce meat consumption and eat more vegetarian or vegan meals.\n"
            "2. Walk, cycle, or use public transport instead of a car.\n"
            "3. Turn off unused appliances and use energy-efficient LED bulbs.\n"
            "4. Recycle and reduce waste to lower your overall footprint."
        )
        return jsonify({"response": predefined_tips})
    # --- End of New Logic ---


    # Prepare context for the model
    context = get_carbon_context(user["id"])
   
    # Create the conversation history with a system prompt
    conversation = [{"role": "system", "content": "You are a helpful AI assistant focused on carbon footprint reduction. Provide encouraging, informative, and actionable advice. Be friendly and conversational."},
                    {"role": "system", "content": f"User Data Context: {context}"},
                    {"role": "user", "content": user_message}]
   
    try:
        # Use the conversational pipeline to generate a response
        conversation_obj = chatbot_pipeline(conversation)
        ai_response = conversation_obj.generated_responses[-1] # Get the latest response
        return jsonify({"response": ai_response})
   
    except Exception as e:
        print(f"An error occurred with the chatbot model: {e}")
        return jsonify({"response": "I'm sorry, I'm having trouble thinking right now. Please try again."}), 500


# ------------------ Auth ------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error":"Username & password required"}),400
    if find_user(username):
        return jsonify({"error":"User exists"}),400
    hashed = generate_password_hash(password)
    create_user(username, hashed)
    return jsonify({"message":"Registered"}),201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    user = find_user(username)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error":"Invalid credentials"}),401
    token = create_access_token(identity=username)
    return jsonify({"access_token": token, "username": username}),200


@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    identifier = data.get("identifier")


    # Here you check user in database
    user = User.query.filter_by(email=identifier).first() or User.query.filter_by(username=identifier).first()


    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404


    # Either send reset email or directly allow setting new password
    # For now, let’s just return success
    return jsonify({"success": True, "message": "Reset link sent"})




# ------------------ Daily Emission ------------------
@app.route("/calculate", methods=["POST"])
@jwt_required()
def calculate():
    username = get_jwt_identity()
    user = find_user(username)
    if not user: return jsonify({"error":"User not found"}),404


    data = request.get_json() or {}
    emissions = total_emission(data)
    date_str = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    add_or_update_entry(user["id"], date_str, {**data, **emissions})
    return jsonify({**data, **emissions, "date": date_str}),200


# ------------------ History ------------------
@app.route("/history", methods=["GET"])
@jwt_required()
def history():
    username = get_jwt_identity()
    user = find_user(username)
    entries = get_entries(user["id"])
    return jsonify({"history": entries}),200


@app.route("/history/30days", methods=["GET"])
@jwt_required()
def history_30_days():
    username = get_jwt_identity()
    user = find_user(username)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    entries = get_entries_since_date(user["id"], start_date.strftime("%Y-%m-%d"))
    return jsonify({"history": entries}),200


# ------------------ Forecast (AI Upgrade) ------------------
@app.route("/forecast", methods=["GET"])
@jwt_required()
def forecast():
    username = get_jwt_identity()
    user = find_user(username)
    entries = get_entries(user["id"])
   
    historical_data = [{"date": e["date"], "total": e["total"]} for e in entries]


    if len(entries) < 3:
        return jsonify({"historical": historical_data, "forecast": None, "message": "Not enough data for a meaningful forecast (need at least 3 entries)."}), 200


    df = pd.DataFrame(entries)
    df['date'] = pd.to_datetime(df['date'])
    df['day_number'] = (df['date'] - df['date'].min()).dt.days
    df['day_of_week'] = df['date'].dt.dayofweek
    df['prev_total'] = df['total'].shift(1)
    df = df.dropna()


    X = df[['day_number', 'day_of_week', 'prev_total']]
    y = df['total']
   
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
   
    last_entry = df.iloc[-1]
    next_day_number = last_entry['day_number'] + 1
    next_day_of_week = (last_entry['day_of_week'] + 1) % 7
    next_prev_total = last_entry['total']
   
    next_day_features = np.array([[next_day_number, next_day_of_week, next_prev_total]])
    pred = float(model.predict(next_day_features)[0])


    return jsonify({"historical": historical_data, "forecast": round(pred, 2)}), 200


# ------------------ Serve frontend ------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
