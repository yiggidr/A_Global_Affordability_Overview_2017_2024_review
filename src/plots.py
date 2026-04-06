import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


def _validate_table(table: str) -> str:
    allowed = {"diet"}
    if table not in allowed:
        raise ValueError(f"Table non autorisée: {table}")
    return table


def plot_missingness(con, table, year_range):
    table = _validate_table(table)
    start_year, end_year = year_range

    df = con.execute(f"""
        SELECT 
            AVG(CASE WHEN cost_healthy_diet_ppp_usd IS NULL THEN 1 ELSE 0 END) AS missing_cost
        FROM {table}
        WHERE year BETWEEN ? AND ?
    """, [start_year, end_year]).df()

    fig, ax = plt.subplots(figsize=(5, 4))
    sns.barplot(x=["cost_healthy_diet_ppp_usd"], y=[df.loc[0, "missing_cost"]], ax=ax, palette="viridis")
    ax.set_title("Part des valeurs manquantes")
    ax.set_ylabel("Taux de valeurs manquantes")
    ax.set_xlabel("")
    ax.set_ylim(0, 1)

    return fig


def plot_trend(con, table, year_range):
    table = _validate_table(table)
    start_year, end_year = year_range

    df = con.execute(f"""
        SELECT year, AVG(cost_healthy_diet_ppp_usd) AS avg_cost
        FROM {table}
        WHERE year BETWEEN ? AND ?
        GROUP BY year
        ORDER BY year
    """, [start_year, end_year]).df()

    fig = px.line(
        df,
        x="year",
        y="avg_cost",
        markers=True,
        title="Évolution du coût moyen d’un healthy diet",
        labels={"year": "Année", "avg_cost": "Coût moyen (PPP USD)"}
    )
    fig.update_layout(template="plotly_white")

    return fig