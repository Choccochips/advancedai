# This file is used to intitialize the database, will not need to run again unless you drop the db again
# DO NOT DELETE THIS FILE MAN PLSSS

import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DUCKDB_PATH", "keeb_data.duckdb")

con = duckdb.connect(DB_PATH)

# landing to having some format
con.execute("""
CREATE TABLE IF NOT EXISTS raw_posts (
    source VARCHAR,
    subreddit VARCHAR,
    post_id VARCHAR PRIMARY KEY,
    permalink VARCHAR,
    url VARCHAR,
    title VARCHAR,
    body VARCHAR,
    author VARCHAR,
    created_utc TIMESTAMP,
    flair_text VARCHAR,
    num_comments INTEGER,
    vote_score INTEGER,
    raw_json JSON
)
""")

# new structure for when items get parsed
con.execute("""
CREATE TABLE IF NOT EXISTS parsed_items (
    post_id VARCHAR,
    item_name VARCHAR,
    item_key VARCHAR,
    price DOUBLE,
    currency VARCHAR,
    is_sold BOOLEAN,
    is_bundle BOOLEAN,
    source_line VARCHAR,
    created_utc TIMESTAMP
)
""")

# keep for check
print(f"Database initialized at {DB_PATH}")
