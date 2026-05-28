# import sqlite3
import pandas as pd
from backend_py.db import connect


def load_studies(sql: str = "SELECT * FROM studies", params: tuple = ()) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def load_all() -> pd.DataFrame:
    return load_studies()
