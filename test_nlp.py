import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"d:\Capstone Project\flight_fare\backend")
from nlp_parser import parse_flight_query

tests = [
    "I want to fly from Vijayawada to Mumbai on Indigo economy",
    "Flight from Tirupati to Delhi on Akasa Air tomorrow",
    "Bagdogra to Bangalore on SpiceJet next Friday",
    "Vizag to Hyderabad on Air India Express in business class",
    "Rajkot to Mumbai on IndiGo in 5 days",
    "Mysore to Chennai on Vistara economy",
    "Shirdi to Pune on Indigo tomorrow",
    "Trichy to Delhi on Air India next Monday",
    "Udaipur to Jaipur on SpiceJet in 3 days",
    "Jodhpur to Delhi on IndiGo business",
]

print("=== NLP PARSER TEST ===")
for q in tests:
    r = parse_flight_query(q)
    status = "OK  " if r["success"] else "FAIL"
    fd = r["flight_data"]
    src = str(fd['source_city'])
    dst = str(fd['destination_city'])
    air = str(fd['airline'])
    cls = fd['travel_class']
    print(f"[{status}] {src:15s} -> {dst:15s} | {air:18s} | {cls}")
    if not r["success"]:
        print(f"       MISSING: {r['missing']}")

print("\n=== DONE ===")
