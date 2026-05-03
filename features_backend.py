# visualize database, just "raw" posts for now

import streamlit as st
import duckdb

st.set_page_config(layout="wide")

con = duckdb.connect("keeb_data.duckdb")

st.title("Landing Reddit Data")

raw_df = con.execute("""
SELECT
    post_id,
    title,
    body,
    created_utc
FROM raw_posts
ORDER BY created_utc DESC
""").fetchdf()

st.subheader("Raw Posts")
st.dataframe(raw_df, use_container_width=True)
