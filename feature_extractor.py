# file is used to get features that will be fed into models

import json
import os
import re
import duckdb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# connects to db and gets Open ai prepped
DB_PATH = os.getenv("DUCKDB_PATH", "keeb_data.duckdb")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

"""

keywords and Regex rules

"""

BRANDS = [
    "keychron", "owlabs", "tgr", "mode", "monokei", "bauer", "rama",
    "kbdfans", "zoom", "neo", "qk", "womier", "luminkey", "elecfox",
    "novelkeys", "tofu", "plume", "zephyr", "matrix", "ai03"
]

LAYOUT_PATTERNS = [
    (r"\b40\b|\b40%\b", "40%"),
    (r"\b60\b|\b60%\b", "60%"),
    (r"\b65\b|\b65%\b", "65%"),
    (r"\b75\b|\b75%\b", "75%"),
    (r"\btkl\b|\b80%\b", "TKL"),
    (r"\bfull[\s-]?size\b|\b100%\b", "Full-size")
]

MATERIAL_PATTERNS = [
    (r"\balu\b|\baluminum\b", "Aluminum"),
    (r"\bpc\b|\bpolycarbonate\b", "Polycarbonate"),
    (r"\bbrass\b", "Brass"),
    (r"\bacrylic\b", "Acrylic"),
    (r"\bsteel\b", "Steel"),
    (r"\bfr4\b", "FR4")
]

PCB_PATTERNS = [
    (r"\bhotswap\b|\bhot swap\b|\bhs\b", "Hotswap"),
    (r"\bsolder\b", "Solder")
]

BUILD_PATTERNS = [
    (r"\bbuilt\b", "Built"),
    (r"\bunbuilt\b|\bbnib\b|\bnew\b", "Unbuilt")
]

CONDITION_PATTERNS = [
    (r"\bflawless\b|\bmint\b", "Mint"),
    (r"\bexcellent\b", "Excellent"),
    (r"\bused\b", "Used"),
    (r"\bscuff\b|\bscuffed\b|\bscratch\b|\bding\b", "Used with flaws")
]


"""

Helper functions 

"""

def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).strip()

#loops through known brands and extracts if present
def extract_brand(text: str):
    t = text.lower()
    for brand in BRANDS:
        if brand in t:
            return brand.title()
    return None

# applies regex rules
def extract_pattern_value(text: str, patterns):
    t = text.lower()
    for pattern, value in patterns:
        if re.search(pattern, t, re.IGNORECASE):
            return value
    return None

# combing item nbame and source line
def regex_extract_features(item_name: str, source_line: str):
    combined = normalize_text(f"{item_name} {source_line}")

    return {
        "brand": extract_brand(combined),
        "layout": extract_pattern_value(combined, LAYOUT_PATTERNS),
        "material": extract_pattern_value(combined, MATERIAL_PATTERNS),
        "pcb_type": extract_pattern_value(combined, PCB_PATTERNS),
        "build_status": extract_pattern_value(combined, BUILD_PATTERNS),
        "condition": extract_pattern_value(combined, CONDITION_PATTERNS),
    }


def needs_ai(features: dict):
    # Use AI only if important fields are missing
    missing_count = sum(1 for v in features.values() if not v)
    return missing_count >= 2


# shoutout openAI
def ai_extract_features(item_name: str, source_line: str):
    prompt = f"""
You are extracting structured product features from a custom keyboard marketplace listing.

Return ONLY valid JSON with this exact schema:
{{
  "brand": "string or null",
  "layout": "40% | 60% | 65% | 75% | TKL | Full-size | null",
  "material": "Aluminum | Polycarbonate | Brass | Acrylic | Steel | FR4 | null",
  "pcb_type": "Hotswap | Solder | null",
  "build_status": "Built | Unbuilt | null",
  "condition": "Mint | Excellent | Used | Used with flaws | null"
}}

Item name:
{item_name}

Source line:
{source_line}
""".strip()

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt
        )
        return json.loads(response.output_text.strip())
    except Exception as e:
        print(f"AI feature extraction failed for '{item_name}': {e}")
        return {
            "brand": None,
            "layout": None,
            "material": None,
            "pcb_type": None,
            "build_status": None,
            "condition": None
        }

# use regex but fallback on ai if needed
def merge_features(regex_features: dict, ai_features: dict):
    merged = {}
    for key in regex_features.keys():
        merged[key] = regex_features.get(key) or ai_features.get(key)
    return merged

"""

Main function

"""
def main():
    con = duckdb.connect(DB_PATH)

    rows = con.execute("""
        SELECT rowid, item_name, source_line
        FROM parsed_items
    """).fetchall()

    updated = 0

    for rowid, item_name, source_line in rows:
        regex_features = regex_extract_features(item_name, source_line)

        if needs_ai(regex_features):
            ai_features = ai_extract_features(item_name, source_line)
        else:

            ai_features = {
                "brand": None,
                "layout": None,
                "material": None,
                "pcb_type": None,
                "build_status": None,
                "condition": None
            }

        final_features = merge_features(regex_features, ai_features)

        con.execute("""
            UPDATE parsed_items
            SET brand = ?,
                layout = ?,
                material = ?,
                pcb_type = ?,
                build_status = ?,
                condition = ?
            WHERE rowid = ?
        """, [
            
            final_features["brand"],
            final_features["layout"],
            final_features["material"],
            final_features["pcb_type"],
            final_features["build_status"],
            final_features["condition"],
            rowid
        ])

        updated += 1

    print(f"Updated {updated} rows with extracted features.")


if __name__ == "__main__":
    main()
