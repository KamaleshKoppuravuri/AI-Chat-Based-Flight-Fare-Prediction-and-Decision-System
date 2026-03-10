import random


# ------------------------------
# PRICE TREND ANALYSIS
# ------------------------------

def analyze_price_trend(predicted_price, days):

    if days <= 7:

        trend_message = "Prices usually increase for last-minute bookings."
        future_price = predicted_price * random.uniform(1.08, 1.15)

    elif days <= 20:

        trend_message = "Prices may fluctuate as the departure date approaches."
        future_price = predicted_price * random.uniform(1.02, 1.08)

    elif days <= 45:

        trend_message = "Prices are moderately stable during this booking window."
        future_price = predicted_price * random.uniform(0.95, 1.05)

    else:

        trend_message = "Early bookings usually offer better deals."
        future_price = predicted_price * random.uniform(0.90, 0.98)

    return trend_message, int(future_price)


# ------------------------------
# BUY / WAIT DECISION ENGINE
# ------------------------------

def get_recommendation(predicted_price, current_price, days):

    price_diff = current_price - predicted_price

    # Big drop expected
    if price_diff > 8000:
        return "WAIT - Price is expected to drop significantly."

    # Moderate drop expected
    elif price_diff > 3000:
        return "WAIT - Price may decrease slightly."

    # Price likely increasing
    elif price_diff < -5000:
        return "BUY NOW - Prices may increase soon."

    # Balanced condition
    else:

        if days <= 7:
            return "BUY NOW - Prices typically increase close to departure."

        elif days <= 30:
            return "WAIT - Monitor prices for a few more days."

        else:
            return "WAIT - Early booking window may provide better deals."


# ------------------------------
# PRICE ALERT SYSTEM
# ------------------------------

def price_alert(predicted_price, current_price):

    difference = current_price - predicted_price

    if difference > 10000:
        return "📉 Major price drop expected."

    elif difference > 4000:
        return "📉 Slight price drop expected."

    elif difference < -8000:
        return "📈 Strong price increase expected."

    elif difference < -3000:
        return "📈 Price may increase soon."

    else:
        return "📊 Prices appear stable."


# ------------------------------
# PRICE TREND SIMULATION
# ------------------------------

def simulate_price_trend(base_price):

    trend = {
        "10_days": int(base_price * random.uniform(1.05, 1.15)),
        "20_days": int(base_price * random.uniform(1.00, 1.10)),
        "30_days": int(base_price * random.uniform(0.95, 1.05)),
        "60_days": int(base_price * random.uniform(0.90, 1.00))
    }

    return trend