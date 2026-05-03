from flask import Flask, render_template, request
import duckdb
import os
import re
import pandas as pd
import joblib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_PATH = os.getenv("DUCKDB_PATH", "keeb_data.duckdb")
MODEL_PATH = os.getenv("MODEL_PATH", "models/best_price_model.joblib")

model = joblib.load(MODEL_PATH)



"""

Keywords/hints 

"""
# running list
KEYBOARD_HINTS = [
    "mode", "envoy", "sonnet", "bauer", "tofu", "zoom", "qk", "matrix",
    "think", "iron", "plume", "zephyr", "glove80", "mercury", "keychron",
    "wooting", "realforce", "hhkb", "kohaku", "f2", "venn", "space65",
    "primus", "physix", "orbit", "u80", "loop", "encore", "casper60",
    "pegasus60", "fc980c", "duo40", "qk75", "tofu65", "luminkey",
    "womier", "filco", "leopold", "drunkdeer", "machina", "rama"
]

ACCESSORY_HINTS = [
    # keycaps
    "keycap", "keycaps", "gmk", "dcs", "kam", "sa ", "mw ",

    # mats / misc
    "deskmat", "desk mat", "mat",

    # artisans --- not enough 
    "artisan", "artisans",

    # switches 
    "switch", "switches","gateron", "gaterons","hmx", "sw ",  "swk","akko",

    # other parts
    "stabs", "stabilizers",
    "foam", "badge", "cable",
    "novelties", "spacebars", "numpad",
    "grab bag", "set", "sets", "kit", "kits"
]

# set up db connect
def get_connection():
    return duckdb.connect(DB_PATH)

"""

helper fxs

"""

def normalize_null(value):
    if value in ("null", "", "None"):
        return None
    return value

def looks_like_accessory(text: str) -> bool:
    if not isinstance(text, str):
        return False

    lowered = text.lower()
    return any(hint in lowered for hint in ACCESSORY_HINTS)

def has_keyboard_pattern(text: str) -> bool:
    if not isinstance(text, str):
        return False

    lowered = text.lower()

    # catches things like common keyboard names layouts included
    if re.search(r"(?:^|\D)(40|45|60|65|75|80|84|87|96|98|100)(?:\D|$)", lowered):
        return True

    # catches layout words 
    if re.search(r"\b(tkl|frl|hhkb|alice|wk|wkl|full[\s-]?size)\b", lowered):
        return True

    return False

def looks_like_keyboard(item) -> bool:
    if isinstance(item, str):
        item_name = item.lower().strip()
        source_line = ""
        layout = None
    else:
        item_name = (item.get("item_name") or "").lower().strip()
        source_line = (item.get("source_line") or "").lower().strip()
        layout = normalize_null(item.get("layout"))

    combined = f"{item_name} {source_line}".strip()

    # harder filter for accessories
    if looks_like_accessory(item_name):
        return False

    #  keyboard signals (ONLY allow these)
    if layout and str(layout).lower() not in ["null", "none", ""]:
        return True

    if any(hint in item_name for hint in KEYBOARD_HINTS):
        return True

    if has_keyboard_pattern(item_name):
        return True

    # last line of defense
    if not looks_like_accessory(combined):
        if any(hint in combined for hint in KEYBOARD_HINTS):
            return True
        if has_keyboard_pattern(combined):
            return True

    return False

# estimates price for each lisitng 
def get_estimated_price(item):
    # UNLESS its an accessory 
    if not looks_like_keyboard(item):
        return item["price"]

    input_df = pd.DataFrame([{
        "brand": normalize_null(item.get("brand")),
        "layout": normalize_null(item.get("layout")),
        "material": normalize_null(item.get("material")),
        "pcb_type": normalize_null(item.get("pcb_type")),
        "build_status": normalize_null(item.get("build_status")),
        "condition": normalize_null(item.get("condition")),
        "is_sold": int(bool(item.get("is_sold", 0))),
        "name_length": len(item.get("item_name") or "")
    }])

    # actual keeb price source
    predicted_price = model.predict(input_df)[0]
    return round(float(predicted_price), 2)

def get_value_label(listed_price, estimated_price, item):
    if not looks_like_keyboard(item):
        return "Accessory", "fair"

    if estimated_price <= 0:
        return "Unknown", "fair"

    ratio = listed_price / estimated_price

    if ratio <= 0.85:
        return "Great Value", "great"
    elif ratio <= 0.95:
        return "Good Value", "fair"
    elif ratio <= 1.10:
        return "Fair Value", "fair"
    else:
        return "Overpriced", "premium"


# main page of my "app"
@app.route("/")
def home():
    # db connec 
    con = get_connection()

    selected_filter = request.args.get("filter", "all")
    # lisitngs get loaded
    query = """
    SELECT
        item_name,
        item_key,
        price,
        is_sold,
        source_line,
        created_utc,
        brand,
        layout,
        material,
        pcb_type,
        build_status,
        condition
    FROM parsed_items
    ORDER BY created_utc DESC
    LIMIT 50
    """

    df = con.execute(query).fetchdf()
    df = df.replace("null", pd.NA)
    listings = df.to_dict(orient="records")

    # add predictions to each item
    for item in listings:
        is_keyboard = looks_like_keyboard(item)
        item["category"] = "keyboard" if is_keyboard else "accessory"

        estimated_price = get_estimated_price(item)
        value_label, value_class = get_value_label(
            item["price"],
            estimated_price,
            item
        )

        item["estimated_price"] = estimated_price
        item["value_label"] = value_label
        item["value_class"] = value_class
        item["difference"] = round(item["price"] - estimated_price, 2)

    if selected_filter == "keyboards":
        listings = [item for item in listings if item["category"] == "keyboard"]
    elif selected_filter == "accessories":
        listings = [item for item in listings if item["category"] == "accessory"]

    return render_template(
        "index.html",
        listings=listings,
        selected_filter=selected_filter
    )
if __name__ == "__main__":
    app.run(debug=True)
