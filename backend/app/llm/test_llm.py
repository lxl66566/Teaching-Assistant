from . import llm


def test_get_models_by_provider():
    models = llm.get_provider_models("openai")
    assert isinstance(models, list)
    assert len(models) > 0
    assert isinstance(models[0], str)
    assert "o1-mini" in models
