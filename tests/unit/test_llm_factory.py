"""Unit tests for LLM Factory and provider strategies."""

import pytest
from src.core.exceptions import ConfigurationError, LLMProviderError
from src.infrastructure.llm.base import BaseLLMProvider
from src.infrastructure.llm.factory import LLMFactory


def test_custom_provider_registration(mock_llm):
    class CustomProvider(BaseLLMProvider):
        def __init__(self, settings=None):
            self.settings = settings

        def create_llm(self, model_name=None, temperature=None, **kwargs):
            return mock_llm

    LLMFactory.register_provider("custom_test", CustomProvider)
    llm = LLMFactory.create(provider="custom_test")
    assert llm is not None


def test_unsupported_provider():
    with pytest.raises(LLMProviderError):
        LLMFactory.create(provider="non_existent_provider_xyz")
