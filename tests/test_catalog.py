import pandas as pd

from benchmark.catalog import validate_result


def test_validate_result_passes_when_rules_are_met():
    # L1_T1 espera exactamente 5 filas y 2 columnas
    df = pd.DataFrame({"Name": ["A", "B", "C", "D", "E"], "AlbumCount": [10, 9, 8, 7, 6]})

    result = validate_result("L1_T1", df)

    assert result["success"] is True
    assert result["details"]["rows_returned"] == 5


def test_validate_result_fails_on_wrong_row_count():
    # L1_T1 espera exactamente 5 filas
    df = pd.DataFrame({"Name": ["A", "B"], "AlbumCount": [10, 9]})

    result = validate_result("L1_T1", df)

    assert result["success"] is False


def test_validate_result_fails_on_execution_error():
    result = validate_result("L1_T1", pd.DataFrame(), error="syntax error")

    assert result["success"] is False
    assert "syntax error" in result["message"]


def test_validate_result_unknown_test_id():
    result = validate_result("NO_EXISTE", pd.DataFrame())

    assert result["success"] is False
    assert result["message"] == "Test no encontrado"
