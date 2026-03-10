import re
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import geodesic



# ── Lookup tables ──────────────────────────────────────────────────────────────



AIRLINE_ALIASES = {
    "indigo": "IndiGo", "6e": "IndiGo", "interglobe": "IndiGo",
    "vistara": "Vistara", "uk": "Vistara",
    "air india": "Air India", "ai": "Air India",
    "air india express": "Air India Express", "ix": "Air India Express",
    "go first": "GO FIRST", "g8": "GO FIRST", "go air": "GO FIRST",
    "airasia": "AirAsia", "air asia": "AirAsia", "i5": "AirAsia",
    "spicejet": "SpiceJet", "sg": "SpiceJet",
    "akasa": "Akasa Air", "qp": "Akasa Air", "akasa air": "Akasa Air",
    "alliance": "Alliance Air", "9i": "Alliance Air",
    "emirates": "Emirates", "ek": "Emirates",
    "qatar": "Qatar Airways", "qatar airways": "Qatar Airways", "qr": "Qatar Airways",
    "singapore airlines": "Singapore Airlines", "sq": "Singapore Airlines",
    "cathay": "Cathay Pacific", "cathay pacific": "Cathay Pacific", "cx": "Cathay Pacific",
    "etihad": "Etihad Airways", "etihad airways": "Etihad Airways", "ey": "Etihad Airways",
    "ana": "ANA All Nippon Airways", "all nippon": "ANA All Nippon Airways", "nh": "ANA All Nippon Airways",
    "jal": "Japan Airlines", "japan airlines": "Japan Airlines", "jl": "Japan Airlines",
    "british airways": "British Airways", "ba": "British Airways",
    "lufthansa": "Lufthansa", "lh": "Lufthansa",
    "air france": "Air France", "af": "Air France",
    "delta": "Delta Airlines", "dl": "Delta Airlines",
    "united": "United Airlines", "ua": "United Airlines",
    "american airlines": "American Airlines", "aa": "American Airlines"
}

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
    "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
}

DAY_NAMES = {
    "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
    "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun",
    "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
    "fri": "Fri", "sat": "Sat", "sun": "Sun"
}



def _find_airline(text):
    lower = text.lower()
    for alias, airline in AIRLINE_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", lower):
            return airline
    for airline in AIRLINES:
        if airline.lower() in lower:
            return airline
    return None

def _find_class_and_multiplier(text):
    lower = text.lower()
    
    # Check for private charter / private fly
    if "private" in lower or "charter" in lower:
        return "Private Charter", 10.0
        
    if "first class" in lower or "first-class" in lower or "firstclass" in lower:
        return "First Class", 3.0
        
    if "premium economy" in lower or "premium-economy" in lower:
        return "Premium Economy", 1.5
        
    if "business" in lower:
        return "Business", 2.0
        
    return "Economy", 1.0

def _find_days_and_day_of_week(text):
    lower = text.lower()
    today = datetime.now()
    
    # 1. Exact Date Matching (e.g. "19th march 2026", "19 march", "march 19")
    month_names = "|".join(MONTHS.keys())
    date_patterns = [
        # 19th march 2026 or 19 march 2026
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(" + month_names + r")\s+(\d{4})",
        # 19th march or 19 march
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(" + month_names + r")",
        # march 19 2026
        r"(" + month_names + r")\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{4})",
        # march 19
        r"(" + month_names + r")\s+(\d{1,2})(?:st|nd|rd|th)?"
    ]
    
    for i, pattern in enumerate(date_patterns):
        m = re.search(pattern, lower)
        if m:
            if i == 0:
                day, month_str, year = int(m.group(1)), m.group(2), int(m.group(3))
            elif i == 1:
                day, month_str, year = int(m.group(1)), m.group(2), today.year
            elif i == 2:
                month_str, day, year = m.group(1), int(m.group(2)), int(m.group(3))
            elif i == 3:
                month_str, day, year = m.group(1), int(m.group(2)), today.year
                
            month = MONTHS[month_str]
            try:
                target_date = datetime(year, month, day)
                # If parsed date is in the past (without explicitly specifying a year), jump to next year
                if target_date < today and (i == 1 or i == 3):
                    target_date = datetime(year + 1, month, day)
                
                days_ahead = (target_date - today).days
                if days_ahead < 0:
                    days_ahead = 0 # Can't book in the past, default to 0
                return days_ahead, target_date.strftime("%a")
            except ValueError:
                pass # Invalid date like Feb 30

    # 2. "tomorrow", "today", "next <weekday>", "within <N> days", etc.
    if "tomorrow" in lower:
        target = today + timedelta(days=1)
        return 1, target.strftime("%a")
    if "today" in lower:
        return 0, today.strftime("%a")

    m = re.search(r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)", lower)
    if m:
        day_str = m.group(1)
        day_abbr = DAY_NAMES[day_str]
        target_weekday = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}[day_abbr]
        days_ahead = (target_weekday - today.weekday() + 7) % 7 or 7
        target = today + timedelta(days=days_ahead)
        return days_ahead, target.strftime("%a")

    m = re.search(r"this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)", lower)
    if m:
        day_str = m.group(1)
        day_abbr = DAY_NAMES[day_str]
        target_weekday = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}[day_abbr]
        days_ahead = (target_weekday - today.weekday()) % 7
        if days_ahead == 0: days_ahead = 7
        target = today + timedelta(days=days_ahead)
        return days_ahead, target.strftime("%a")

    m = re.search(r"within\s+(\d+)\s+days?", lower)
    if m:
        n = int(m.group(1))
        target = today + timedelta(days=n)
        return n, target.strftime("%a")

    m = re.search(r"in\s+(\d+)\s+days?", lower)
    if m:
        n = int(m.group(1))
        target = today + timedelta(days=n)
        return n, target.strftime("%a")

    m = re.search(r"(\d+)\s+days?", lower)
    if m:
        n = int(m.group(1))
        target = today + timedelta(days=n)
        return n, target.strftime("%a")

    m = re.search(r"on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)", lower)
    if m:
        day_str = m.group(1)
        day_abbr = DAY_NAMES[day_str]
        target_weekday = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}[day_abbr]
        days_ahead = (target_weekday - today.weekday() + 7) % 7 or 7
        target = today + timedelta(days=days_ahead)
        return days_ahead, target.strftime("%a")

    target = today + timedelta(days=14)
    return 14, target.strftime("%a")

def _extract_route(text):
    lower = text.lower()
    terminators = r"(?:\s+on\b|\s+in\b|\s+for\b|\s+within\b|\s+tomorrow\b|\s+today\b|\s+next\b|\s+this\b|\s+with\b|\s+departing\b|\s*\b\d|\s*$)"
    
    # Try direct pattern: from X to Y
    m = re.search(r"\bfrom\s+([A-Za-z\s.,-]+?)\s+to\s+([A-Za-z\s.,-]+?)(?=" + terminators + r")", lower)
    if m:
        return m.group(1).strip().title(), m.group(2).strip().title()

    # Try pattern: X to Y
    m = re.search(r"\b([A-Za-z\s.,-]+?)\s+to\s+([A-Za-z\s.,-]+?)(?=" + terminators + r")", lower)
    if m:
        return m.group(1).strip().title(), m.group(2).strip().title()

    return None, None

def parse_flight_query(text):
    source, destination = _extract_route(text)
    lower = text.lower()
    
    airline = _find_airline(text)
    travel_class, price_multiplier = _find_class_and_multiplier(text)
    
    if travel_class == "Private Charter" and not airline:
        airline = "Private Jet"
        
    days_to_departure, day_of_week = _find_days_and_day_of_week(text)

    # Dynamic Location and Distance Integration using geopy
    is_international = 0
    distance_km = 1200.0  # Default baseline distance if geocoding fails
    
    if source and destination:
        try:
            geolocator = Nominatim(user_agent="flight_fare_app")
            loc_source = geolocator.geocode(source, timeout=5)
            loc_dest = geolocator.geocode(destination, timeout=5)
            
            if loc_source and loc_dest:
                addr_source_parts = [p.strip() for p in loc_source.address.split(',')]
                addr_dest_parts = [p.strip() for p in loc_dest.address.split(',')]
                
                source = addr_source_parts[0]
                destination = addr_dest_parts[0]
                
                country_source = addr_source_parts[-1]
                country_dest = addr_dest_parts[-1]
                
                if country_source != country_dest:
                    is_international = 1
                    
                distance_km = geodesic((loc_source.latitude, loc_source.longitude), 
                                       (loc_dest.latitude, loc_dest.longitude)).km
        except Exception as e:
            print(f"Geocoding error: {e}")
            
    # Scale price based on actual geographical distance
    # Assume 1200 km is the baseline domestic multiplier = 1.0x
    distance_multiplier = max(0.5, distance_km / 1200.0)
    
    if is_international:
        price_multiplier *= 1.5  # base international premium
        
    price_multiplier *= distance_multiplier

    missing = []
    if not source: missing.append("source city/country")
    if not destination: missing.append("destination city/country")
    if not airline: missing.append("airline")

    # The actual data shown in Chat UI
    flight_data_display = {
        "source_city": source,
        "destination_city": destination,
        "airline": airline,
        "travel_class": travel_class,
        "is_international": is_international,
        "days_to_departure": days_to_departure,
        "day_of_week": day_of_week
    }
    
    # The safe data passed to the ML Model
    safe_class = "Business" if travel_class in ["Business", "First Class", "Private Charter"] else "Economy"
    safe_airline = airline if airline in ["Vistara", "Air India", "IndiGo", "GO FIRST", "AirAsia", "SpiceJet"] else "Vistara"
    
    # We pass the dynamic unknown cities straight into the model array. 
    # OneHotEncoder will set unknown values to 0 dynamically, allowing custom predictions!
    model_data = {
        "source_city": source if source else "Delhi",
        "destination_city": destination if destination else "Mumbai",
        "airline": safe_airline,
        "travel_class": safe_class,
        "is_international": 0, # Model doesn't handle 1 properly
        "days_to_departure": days_to_departure,
        "day_of_week": day_of_week
    }

    # Add specific date info to interpreted text if available
    date_str = (datetime.now() + timedelta(days=days_to_departure)).strftime("%d %b %Y")
    
    interpreted = (
        f"💡 Parsed: Flying from {source or '[?]'} to {destination or '[?]'} "
        f"on {airline or '[?]'} in {travel_class} class, "
        f"departing on {date_str} ({days_to_departure} day(s) from now)."
    )

    return {
        "success": len(missing) == 0,
        "missing": missing,
        "flight_data": flight_data_display,
        "model_data": model_data,
        "price_multiplier": price_multiplier,
        "interpreted_text": interpreted
    }
