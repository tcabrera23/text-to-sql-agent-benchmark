from core.metrics import calculate_cost, calculate_efficiency


def test_calculate_cost_known_model():
    # 1,000,000 tokens de entrada y 1,000,000 de salida a los precios de gpt-4o
    cost = calculate_cost("openai/gpt-4o", tokens_input=1_000_000, tokens_output=1_000_000)

    assert cost == 12.50  # $2.50 input + $10.00 output


def test_calculate_cost_free_model_is_zero():
    cost = calculate_cost("microsoft/phi-3.5-mini-128k-instruct", tokens_input=5000, tokens_output=5000)

    assert cost == 0.0


def test_calculate_cost_unknown_model_defaults_to_zero():
    cost = calculate_cost("modelo/inexistente", tokens_input=1000, tokens_output=1000)

    assert cost == 0.0


def test_calculate_cost_price_override_ignores_pricing_table():
    # Modelo agregado a mano desde la UI del Arena: no está en MODEL_PRICING,
    # así que debe usar el precio manual en vez de devolver 0.
    cost = calculate_cost(
        "custom/unlisted-model",
        tokens_input=1_000_000,
        tokens_output=1_000_000,
        price_override={"input": 1.0, "output": 2.0},
    )

    assert cost == 3.0


def test_calculate_cost_price_override_wins_over_known_model():
    # Si se pasa price_override, tiene prioridad incluso para un modelo que
    # sí figura en MODEL_PRICING.
    cost = calculate_cost(
        "openai/gpt-4o",
        tokens_input=1_000_000,
        tokens_output=1_000_000,
        price_override={"input": 0.0, "output": 0.0},
    )

    assert cost == 0.0


def test_calculate_efficiency_tokens_per_second():
    efficiency = calculate_efficiency(tokens_processed=200, execution_time=2.0)

    assert efficiency == 100.0


def test_calculate_efficiency_zero_time_does_not_divide_by_zero():
    assert calculate_efficiency(tokens_processed=200, execution_time=0) == 0.0
