from core.database import execute_sql


def test_valid_select_returns_dataframe_without_error():
    df, error = execute_sql("SELECT * FROM artists LIMIT 5")

    assert error is None
    assert len(df) == 5
    assert "Name" in df.columns


def test_with_cte_is_allowed():
    df, error = execute_sql("WITH t AS (SELECT * FROM genres) SELECT * FROM t LIMIT 3")

    assert error is None
    assert len(df) == 3


def test_non_select_query_is_rejected():
    df, error = execute_sql("DROP TABLE albums")

    assert df.empty
    assert error == "Solo se permiten consultas SELECT."


def test_invalid_sql_returns_error_instead_of_raising():
    df, error = execute_sql("SELECT * FROM tabla_que_no_existe")

    assert df.empty
    assert error is not None
