import requests

url = "http://127.0.0.1:5000/predict"

data = {
    "source_city": "Bangalore",
    "destination_city": "London",
    "airline": "British Airways",
    "travel_class": "Business",
    "is_international": 1,
    "days_to_departure": 20,
    "day_of_week": "Mon"
}

print("Sending POST request to /predict ...")

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("Response Text:", response.text)

try:
    print("Response JSON:", response.json())
except:
    print("Response is not JSON")
