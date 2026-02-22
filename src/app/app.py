import streamlit as st
from src.data.load_data import load_dataset
from src.plots.charts import plot_trend

st.set_page_config(layout="wide")

st.title("Global Healthy Diet Affordability Dashboard")

df = load_dataset()

# Sidebar filters
countries = st.sidebar.multiselect(
    "Select countries",
    options=sorted(df["country"].unique()),
    default=[df["country"].unique()[0]]
)

years = st.sidebar.slider(
    "Select year range",
    int(df["year"].min()),
    int(df["year"].max()),
    (2018, 2023)
)

filtered_df = df[
    (df["country"].isin(countries)) &
    (df["year"].between(years[0], years[1]))
]

st.dataframe(filtered_df.head())

st.plotly_chart(plot_trend(filtered_df), use_container_width=True)