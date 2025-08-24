import os, argparse
import pandas as pd
from joblib import dump, load
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "waste_model.joblib")

"""
Expected CSV columns for training:
  name, category, days_to_expiry, quantity, previously_wasted_rate, wasted (0/1)
"""

def train(csv_path):
    df = pd.read_csv(csv_path)
    y = df["wasted"].astype(int)
    X = df.drop(columns=["wasted"])

    cat_cols = ["category", "name"]
    num_cols = [c for c in X.columns if c not in cat_cols]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ("num", "passthrough", num_cols)
    ])

    pipe = Pipeline([
        ("prep", pre),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:,1]
    auc = roc_auc_score(y_test, proba)
    print(f"AUC: {auc:.3f}")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    dump(pipe, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

def predict(features: dict) -> float:
    if not os.path.exists(MODEL_PATH):
        # simple rule-based fallback
        dte = features.get("days_to_expiry", 7)
        qty = features.get("quantity", 1)
        base = 0.2
        if dte <= 3:
            base += 0.5
        if qty >= 3:
            base += 0.1
        return max(0.0, min(1.0, base))
    model = load(MODEL_PATH)
    import pandas as pd
    row = pd.DataFrame([features])
    p = model.predict_proba(row)[:,1][0]
    return float(p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", help="Path to history CSV", default=None)
    args = ap.parse_args()
    if args.train:
        train(args.train)
    else:
        print("Usage: python model.py --train data/history.csv")
