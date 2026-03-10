import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_csv("D:/Capstone Project/flight_fare/data/flight_fare_dataset.csv")

X = df.drop("final_price", axis=1)
y = df["final_price"]

categorical_features = [
    "source_city","destination_city",
    "airline","travel_class","day_of_week"
]

numerical_features = ["is_international","days_to_departure"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ("num", "passthrough", numerical_features)
])

model = GradientBoostingRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=3,
    random_state=42
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("GB MAE:", mae)
print("GB RMSE:", rmse)

joblib.dump(
    pipeline,
    r"D:/Capstone Project/flight_fare/models/price_model_gb.pkl"
)

print("Model trained & saved!")
