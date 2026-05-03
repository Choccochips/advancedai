"""

This script pulls cleaned keyboard listings from our database, filters out noise, and trains two machine learning models to predict price. 
It uses a preprocessing pipeline to handle both categorical and numeric features, then compares models using error metrics. This part was created 
in collaboration with Bret Harvestine, an old coworker from Delta Defense. He had some pointers on ML and how to create a more robust system, so I took
him up on his help. 

Some of the techniques did come from him, but the work is my own and worked with me. He did not do anything for me. 


"""

import os
import joblib
import duckdb
import pandas as pd

# sk learn for the machine learning models and stuff
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

import re

# path for our duckdb (local) db
DB_PATH = os.getenv("DUCKDB_PATH", "keeb_data.duckdb")

# where we will be putting our trained models
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# just keywords for simpler recognition 
KEYBOARD_HINTS = [
    "mode", "envoy", "sonnet", "bauer", "tofu", "zoom", "qk", "matrix",
    "think", "iron", "plume", "zephyr", "glove80", "mercury", "keychron",
    "wooting", "realforce", "hhkb", "kohaku", "f2", "venn", "space65",
    "primus", "physix", "orbit", "u80", "loop", "encore", "casper60",
    "pegasus60", "fc980c", "duo40", "qk75", "tofu65", "tkl",
    "luminkey", "womier", "filco", "leopold", "drunkdeer", "machina", "rama"
]

def looks_like_keyboard(name: str) -> bool:
    if not isinstance(name, str):
        return False

    lowered = name.lower().strip()

    # keyword matching
    if any(hint in lowered for hint in KEYBOARD_HINTS):
        return True

    # regex for common keyboard layout/size patterns
    if re.search(r"(?:^|\D)(40|45|60|65|75|80|84|87|96|98|100)(?:\D|$)", lowered):
        return True

    # regex for layout keywords
    if re.search(r"\b(tkl|frl|hhkb|alice|wk|wkl|full[\s-]?size)\b", lowered):
        return True

    return False

# laod and clean data 
def load_training_data():
    con = duckdb.connect(DB_PATH)

    df = con.execute("""
        SELECT
            post_id,
            item_name,
            price,
            is_sold,
            brand,
            layout,
            material,
            pcb_type,
            build_status,
            condition
        FROM parsed_items
        WHERE price IS NOT NULL
    """).df()

    df = df.replace("null", pd.NA)
    df = df.replace("", pd.NA)

    # keep only rows with items that "look like keyboard"
    df = df[df["item_name"].apply(looks_like_keyboard)].copy()
    df = df[(df["price"] >= 20) & (df["price"] <= 2000)].copy()

    # just to get length of name
    df["name_length"] = df["item_name"].fillna("").apply(len)

    return df

def train_models(df: pd.DataFrame):
    possible_categorical = [
        "brand",
        "layout",
        "material",
        "pcb_type",
        "build_status",
        "condition",
    ]

    possible_numeric = [
        "is_sold",
        "name_length",
    ]

    # keep columns that have at least one non-null value
    categorical_features = [
        col for col in possible_categorical
        if col in df.columns and df[col].notna().any()
    ]

    numeric_features = [
        col for col in possible_numeric
        if col in df.columns and df[col].notna().any()
    ]

    feature_cols = categorical_features + numeric_features

    # check 
    print("Using feature columns:", feature_cols)

    X = df[feature_cols]
    y = df["price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=67
    )

    transformers = []

    # will handle categorical dataa AKA strings 
    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore"))
                ]),
                categorical_features
            )
        )

    # handles numerical features
    if numeric_features:
        transformers.append(
            (
                "num",
                Pipeline(steps=[
                    ("imputer", SimpleImputer(strategy="median"))
                ]),
                numeric_features
            )
        )

    # combine the preprocessing steps 
    preprocessor = ColumnTransformer(transformers=transformers)

    # the tewo models I will be using, rf and linear as baseline
    models = {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=200,
            random_state=67
        )
    }

    results = {}

    for model_name, model in models.items():
        pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        # actual magic happening here
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)

        results[model_name] = {
            "pipeline": pipeline,
            "mae": mae,
            "r2": r2,
            "feature_cols": feature_cols
        }

        joblib.dump(pipeline, os.path.join(MODEL_DIR, f"{model_name}.joblib"))

    return results

def main():
    df = load_training_data()

    print("Training rows:", len(df))
    print(df[["item_name", "price", "brand", "layout", "material"]].head(10))

    # early stop if the data is light 
    if len(df) < 10:
        print("Not enough rows to train yet.")
        return

    results = train_models(df)

    # results
    print("\nModel results:")
    for model_name, info in results.items():
        print(f"{model_name}:")
        print(f"  MAE: {info['mae']:.2f}")
        print(f"  R2:  {info['r2']:.4f}")

    best_model_name = min(results, key=lambda k: results[k]["mae"])
    best_pipeline = results[best_model_name]["pipeline"]

    # saving the best model seperately 
    joblib.dump(best_pipeline, os.path.join(MODEL_DIR, "best_price_model.joblib"))
    print(f"\nSaved best model as: models/best_price_model.joblib")
    print(f"Best model: {best_model_name}")

if __name__ == "__main__":
    main()
