import json
import os
import re
import duckdb
from dotenv import load_dotenv
from openai import OpenAI

# load credentials
load_dotenv()

# db path and openai name
DB_PATH = os.getenv("DUCKDB_PATH", "keeb_data.duckdb")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# NEEDED, open up for openai use later if we get that far in script
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# this is regex for pricing 
PRICE_RE = re.compile(
    r'(?i)(?:\$\s*([0-9]{2,5}(?:\.[0-9]{1,2})?)|([0-9]{2,5}(?:\.[0-9]{1,2})?)\s*\$|\busd\s*([0-9]{2,5}(?:\.[0-9]{1,2})?))'
)

# regex for reddit tags like [Sold]
SOLD_RE = re.compile(r'(?i)\b(sold|pending)\b')

# junk removal 
URL_RE = re.compile(r'(?i)\bhttps?://\S+|\bimgur\.com/\S+')


"""

Keywords/hints section 

"""

STOPWORDS = {
    "paypal", "pp", "conus", "timestamp", "timestamps", "shipping", "shipped",
    "obo", "wts", "wtt", "w", "h", "lf", "looking", "looking for",
    "price", "pricing", "asking", "bundle", "bundles", "each",
    "pm", "comment", "before", "trade", "trades", "sold", "pending"
}

BAD_KEYS = {
    "asking", "price", "pricing", "bundle", "looking", "looking for",
    "paypal", "shipping", "shipped", "timestamps", "timestamp", "original",
    "base", "switches", "keyboard", "keyboards", "keycaps", "deskmat",
    "deskmats", "artisan", "artisans"
}

SECTION_HINTS = {
    "keyboard", "keyboards", "keycaps", "switches", "deskmat", "deskmats",
    "artisan", "artisans", "misc", "extras"
}

BAD_PHRASES = {
    "with free",
    "choose between",
    "comment before pm",
    "open to offers",
    "all prices are shipped",
    "prices do not include shipping",
    "extra screws",
    "extra daughterboard",
    "extra aluminum plate",
    "free gmk set",
    "obo",
    "or best offer",
    "chat"
}

"""

functions

"""

# removes links and helps with spacing 
def normalize_text(s: str) -> str:
    s = (s or "").strip()
    s = URL_RE.sub(" ", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

# simple filter to toss buying posts since we wont need that for this model
def is_buying_post(title: str) -> bool:
    t = (title or "").lower()

    if "[h] paypal [w]" in t:
        return True
    if "[h] cash [w]" in t:
        return True
    if "[h] venmo [w]" in t:
        return True

    if "[h]" in t and "[w]" in t:
        h_pos = t.find("[h]")
        w_pos = t.find("[w]")
        h_section = t[h_pos:w_pos] if h_pos != -1 and w_pos != -1 and w_pos > h_pos else ""
        if "paypal" in h_section or "cash" in h_section or "venmo" in h_section:
            return True

    return False

# to ignore bundles 
def is_bundleish(line: str) -> bool:
    l = line.lower()
    return any(k in l for k in [
        "bundle", "take all", "all for", "for everything",
        "everything for", "lot for", "take all switches"
    ])

# skips 
def is_section_header(line: str) -> bool:
    l = normalize_text(line).lower().strip(": -")
    return l in SECTION_HINTS

#skips more garbage 
def is_garbage_line(line: str) -> bool:
    l = line.lower().strip()
    if not l:
        return True
    if URL_RE.search(l):
        return True
    if len(re.sub(r"[a-z0-9]", "", l)) > len(l) * 0.75:
        return True
    return False


def extract_price(line: str):
    m = PRICE_RE.search(line)
    if not m:
        return None

    for g in m.groups():
        if g:
            try:
                return int(float(g))
            except ValueError:
                return None
    return None

# LOT of cleaning for NAMESSSSS: removes a lot like prices, status, and other noise. standardizes names 
def clean_item_candidate(s: str) -> str:
    s = normalize_text(s)
    s = s.replace("~~", "")
    s = re.sub(r"^[\-\*\u2022]+\s*", "", s)
    s = s.strip(" |:-\t")
    s = SOLD_RE.sub("", s)
    s = re.sub(r"(?i)\b(?:usd)\b", " ", s)
    s = re.sub(r"\$\s*[0-9]{2,5}(?:\.[0-9]{1,2})?", " ", s)
    s = re.sub(r"[0-9]{2,5}(?:\.[0-9]{1,2})?\s*\$", " ", s)
    s = re.sub(r"(?i)\bshipped\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    if len(s) > 120:
        s = s[:120].rstrip()

    return s


def make_item_key(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"\[[^\]]*\]", " ", s)

    for w in STOPWORDS:
        s = re.sub(rf"\b{re.escape(w)}\b", " ", s)

    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# some more validaiton with simple fiters to toss words/phrases that are more than likely trash
def looks_like_real_item(item_name: str, item_key: str) -> bool:
    if not item_name or not item_key:
        return False
    if len(item_key) < 3:
        return False
    if item_key in BAD_KEYS:
        return False
    if URL_RE.search(item_name.lower()):
        return False
    if len(item_key.split()) > 10:
        return False
    if item_key in {"original", "base", "switches", "keycaps", "keyboard", "keyboards"}:
        return False
    return True

# catch paser mistakes, another filter and triggers openai
def looks_like_weak_name(item_name: str) -> bool:
    if not item_name:
        return True

    lowered = item_name.lower().strip()

    if lowered in SECTION_HINTS:
        return True

    if any(p in lowered for p in BAD_PHRASES):
        return True

    # too generic or badly clipped
    if lowered.endswith(" x"):
        return True
    if lowered.startswith("with free"):
        return True
    if lowered.startswith("choose between"):
        return True
    if lowered.startswith("extra "):
        return True

    return False


def extract_item_from_price_line(line: str) -> str:
    raw = normalize_text(line)

    if "|" in raw:
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        if parts:
            return clean_item_candidate(parts[0])

    m = PRICE_RE.search(raw)
    if not m:
        return ""

    start = m.start()
    end = m.end()

    left = raw[:start].strip()
    right = raw[end:].strip()

    candidate = clean_item_candidate(left)

    if len(candidate) < 3 or is_section_header(candidate):
        candidate = clean_item_candidate(right)

    return candidate


# throws LLM at the problem to help with any shortcomings. 
def ai_cleanup_line(title: str, line: str, extracted_price: int):
    """
    Uses OpenAI only when regex extraction looks weak, may tweak in future
    """
    prompt = f"""
You are cleaning a single marketplace listing line from a custom keyboard trading post.

Your job:
- infer the best item name from this ONE line
- do not invent a price
- do not include sold/pending in the name
- do not include filler like "with free gmk set", "choose between", "extra", "comment before pm"
- if the line is not a real sellable item row, return skip=true

Return ONLY valid JSON in this exact shape:
{{
  "item_name": "string",
  "skip": true_or_false
}}

Post title:
{title}

Listing line:
{line}

Extracted price:
{extracted_price}
""".strip()

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt
        )

        text = response.output_text.strip()
        data = json.loads(text)

        item_name = normalize_text(data.get("item_name", ""))
        skip = bool(data.get("skip", False))

        return {
            "item_name": item_name,
            "skip": skip
        }
    except Exception as e:
        print(f"AI cleaning failed for line: {line} | error: {e}")
        return {
            "item_name": "",
            "skip": False
        }

# main engine here - calls all my fxs to make things pretty. or toss
def parse_post(body: str, title: str):
    results = []
    if not body:
        return results

    if is_buying_post(title):
        return results

    title_clean = normalize_text(title)
    title_key = make_item_key(title_clean)

    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]

    for ln in lines:
        if is_garbage_line(ln):
            continue

        if is_section_header(ln):
            continue

        if is_bundleish(ln):
            continue

        price = extract_price(ln)
        if price is None:
            continue

        sold = bool(SOLD_RE.search(ln)) or ("~~" in ln)

        item_name = extract_item_from_price_line(ln)
        item_key = make_item_key(item_name)

        # OpenAI fallback only for weak names
        if looks_like_weak_name(item_name) or not looks_like_real_item(item_name, item_key):
            ai_result = ai_cleanup_line(title_clean, ln, price)

            if ai_result.get("skip"):
                continue

            ai_name = ai_result.get("item_name", "")
            if ai_name:
                item_name = ai_name
                item_key = make_item_key(item_name)

        item_name = item_name.title()
        item_key = make_item_key(item_name)     

        # Final fallback
        if not looks_like_real_item(item_name, item_key):
            item_name = title_clean
            item_key = title_key

        if not looks_like_real_item(item_name, item_key):
            continue

        if len(item_key.split()) > 12:
            continue

        lower_name = item_name.lower()
        if any(bad_phrase in lower_name for bad_phrase in BAD_PHRASES):
            continue

        results.append({
            "item_name": item_name,
            "item_key": item_key,
            "price": price,
            "is_sold": sold,
            "is_bundle": False,
            "source_line": normalize_text(ln)
        })

    return results

# loads posts from db and gets things rolling
def main():
    con = duckdb.connect(DB_PATH)

    LIMIT = 1000

    rows = con.execute("""
        SELECT post_id, title, body, created_utc
        FROM raw_posts
        ORDER BY created_utc DESC
        LIMIT ?
    """, [LIMIT]).fetchall()

    inserted = 0

    con.execute("DELETE FROM parsed_items")

    for post_id, title, body, created_utc in rows:
        parsed = parse_post(body, title)

        for r in parsed:
            con.execute("""
                INSERT INTO parsed_items (
                    post_id, item_name, item_key,
                    price, currency,
                    is_sold, is_bundle,
                    source_line, created_utc
                )
                VALUES (?, ?, ?, ?, 'USD', ?, ?, ?, ?)
            """, [
                post_id,
                r["item_name"],
                r["item_key"],
                r["price"],
                r["is_sold"],
                r["is_bundle"],
                r["source_line"],
                created_utc
            ])
            inserted += 1

    print(f"Done. Inserted {inserted} rows into parsed_items.")


if __name__ == "__main__":
    main()
