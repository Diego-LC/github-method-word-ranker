"""Streamlit scaffold for the ranking UI."""

import streamlit as st


st.set_page_config(page_title="GitHub Method Word Ranker", layout="wide")

st.title("GitHub Method Word Ranker")
st.caption("Initial visualizer scaffold")
st.info("Realtime ranking UI is pending implementation.")

st.subheader("Planned behavior")
st.markdown("- Read aggregate ranking data from Redis.")
st.markdown("- Render a top-N view and summary metrics.")
st.markdown("- Refresh automatically every few seconds.")
