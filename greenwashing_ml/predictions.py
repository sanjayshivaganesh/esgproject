import joblib

model = joblib.load("model.pkl")

examples = [
    "We aim to achieve net zero emissions by 2040",
    "Scope 1 emissions decreased by 12% in FY25",
    "The report follows the GHG Protocol"
]

for text in examples:
    prediction = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]

    print()
    print(text)
    print("Prediction:", prediction)
    print("Confidence:", max(probabilities))