def _validate_table(table: str) -> str:
    allowed = {"diet"}
    if table not in allowed:
        raise ValueError(f"Table non autorisée: {table}")
    return table


def summary_statistics(con, table, year_range):
    table = _validate_table(table)
    start_year, end_year = year_range

    query = f"""
    SELECT 
        COUNT(*) AS total_rows,
        ROUND(AVG(cost_healthy_diet_ppp_usd), 2) AS avg_cost,
        ROUND(MIN(cost_healthy_diet_ppp_usd), 2) AS min_cost,
        ROUND(MAX(cost_healthy_diet_ppp_usd), 2) AS max_cost
    FROM {table}
    WHERE year BETWEEN ? AND ?
    """

    return con.execute(query, [start_year, end_year]).df()