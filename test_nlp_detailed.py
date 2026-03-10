import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"d:\Capstone Project\flight_fare\backend")
from nlp_parser import parse_flight_query
from pprint import pprint

tests = [
    "I want a flight from sri lanka to chennai on 19th march 2026 on indigo",
    "Flight from bangkok to dubai on emirates first class tomorrow",
    "bhutan to nepal on qatar airways business class 12 oct",
    "I want to fly from america to london on british airways premium economy",
    "private charter from sydney to auckland on 5th august",
]

print("=== NLP PARSER TEST ===")
for q in tests:
    print(f"\nQUERY: {q}")
    r = parse_flight_query(q)
    if not r["success"]:
        print(f"FAIL -> Missing: {r['missing']}\n  Found: {r['flight_data']}")
    else:
        print("SUCCESS!")
        fd = r['flight_data']
        md = r['model_data']
        print(f"  Display : {fd['source_city']} -> {fd['destination_city']} | {fd['airline']} | {fd['travel_class']}")
        print(f"  Model   : {md['source_city']} -> {md['destination_city']} | {md['airline']} | {md['travel_class']}")
        print(f"  Multiplier: {r['price_multiplier']}")
        print(f"  Message : {r['interpreted_text']}")
