import streamlit as st
from db import get_connection
from analysis import summary_statistics
from plots import plot_missingness, plot_trend

st.set_page_config(page_title="Diet Dashboard", layout="wide")
st.title("🌍 Diet Dashboard")

@st.cache_resource
def init_db():
    return get_connection()

con = init_db()

st.sidebar.header("Filtres")
years = st.sidebar.slider("Année", 2017, 2024, (2017, 2024))

st.subheader(" Overview")
stats = summary_statistics(con, "diet", years)
st.dataframe(stats, use_container_width=True)

st.subheader(" Missing values")
fig1 = plot_missingness(con, "diet", years)
st.pyplot(fig1)

st.subheader(" Trends")
fig2 = plot_trend(con, "diet", years)
st.plotly_chart(fig2, use_container_width=True)