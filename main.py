from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import uuid

from decision_engine import (
    analyze_price_trend,
    get_recommendation,
    price_alert,
    simulate_price_trend
)
from nlp_parser import parse_flight_query
from database import save_chat_message, get_chat_history

app = FastAPI(title="Flight Fare API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=== LOADING FASTAPI APP ===")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "price_model_gb.pkl")

# Load model
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    model = None

# Pydantic models for request validation
class FlightQuery(BaseModel):
    source_city: str
    destination_city: str
    airline: str
    travel_class: str
    is_international: int
    days_to_departure: int
    day_of_week: int

class NLPQuery(BaseModel):
    text: str
    session_id: str = "default_session"

@app.get("/")
def home():
    INDEX_PATH = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"message": "Flight Fare Analysis API is running! (Frontend not found)"}

@app.post("/predict")
def predict(query: FlightQuery):
    print(">>> /predict route HIT")

    data = query.dict()
    df = pd.DataFrame([data])
    predicted_price = model.predict(df)[0]
    
    current_price = predicted_price * 1.07
    trend_simulation = simulate_price_trend(predicted_price)
    
    days = data["days_to_departure"]
    trend_message, future_price = analyze_price_trend(predicted_price, days)
    recommendation = get_recommendation(predicted_price, current_price, days)
    alert = price_alert(predicted_price, current_price)

    chat_message = (
        f"✈️ Flight: {data['source_city']} → {data['destination_city']}\n"
        f"🛫 Airline: {data['airline']} | Class: {data['travel_class']}\n\n"
        f"💰 Predicted Fare: ₹{int(predicted_price)}\n"
        f"📊 Current Market Fare: ₹{int(current_price)}\n\n"
        f"📈 Trend Insight: {trend_message}\n\n"
        f"🤖 Recommendation: {recommendation}\n\n"
        f"{alert}"
    )

    return {
        "predicted_price": int(predicted_price),
        "current_price": int(current_price),
        "trend_analysis": trend_message,
        "future_estimate": int(future_price),
        "price_trend": trend_simulation,
        "recommendation": recommendation,
        "alert": alert,
        "chat_message": chat_message
    }

@app.post("/parse_and_predict")
async def parse_and_predict(query: NLPQuery):
    print(f">>> /parse_and_predict route HIT (Session: {query.session_id})")
    raw_text = query.text
    
    # Save user message to database
    await save_chat_message(query.session_id, raw_text, "user")
    
    # 1. Parse the text
    parsed_result = parse_flight_query(raw_text)
    
    if not parsed_result["success"]:
        missing_str = ", ".join(parsed_result["missing"])
        error_msg = f"I couldn't quite understand all the flight details. I am missing: {missing_str}. Please provide a complete sentence (e.g., 'Flight from Delhi to Mumbai on Vistara')."
        
        # Save bot response to database
        await save_chat_message(query.session_id, error_msg, "bot")
        
        raise HTTPException(status_code=400, detail={"success": False, "error_msg": error_msg})
        
    flight_data = parsed_result["flight_data"]
    model_data = parsed_result["model_data"]
    price_multiplier = parsed_result["price_multiplier"]
    interpreted_message = parsed_result["interpreted_text"]
    
    # 2. Predict Price
    df = pd.DataFrame([model_data])
    predicted_price = model.predict(df)[0] * price_multiplier

    # 3. Simulate and Analyze
    current_price = predicted_price * 1.07
    trend_simulation = simulate_price_trend(predicted_price)
    
    days = flight_data["days_to_departure"]
    trend_message, future_price = analyze_price_trend(predicted_price, days)
    recommendation = get_recommendation(predicted_price, current_price, days)
    alert = price_alert(predicted_price, current_price)
    
    response_payload = {
        "success": True,
        "flight_data": flight_data,
        "interpreted_message": interpreted_message,
        "predicted_price": int(predicted_price),
        "current_price": int(current_price),
        "trend_analysis": trend_message,
        "future_estimate": int(future_price),
        "price_trend": trend_simulation,
        "recommendation": recommendation,
        "alert": alert
    }
    
    # Create the bot message text for history
    chat_message = (
        f"Understood: {interpreted_message}\n\n"
        f"💰 Predicted Fare: ₹{int(predicted_price)}\n"
        f"📊 Current Market Fare: ₹{int(current_price)}\n"
        f"📈 Trend Insight: {trend_message}\n"
        f"🤖 Recommendation: {recommendation}\n"
        f"{alert}"
    )
    
    # Save bot response to database
    await save_chat_message(query.session_id, chat_message, "bot")
    
    return response_payload

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Fetch chat history for a given session."""
    messages = await get_chat_history(session_id)
    return {"session_id": session_id, "history": messages}

if __name__ == "__main__":
    import uvicorn
    print("=== STARTING FASTAPI SERVER ===")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
