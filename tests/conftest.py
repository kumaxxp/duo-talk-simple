# tests/conftest.py

import pytest
import shutil
import os
from core.ollama_client import OllamaClient


@pytest.fixture(scope="session")
def ollama_client():
    """セッション全体で共有するOllamaClient"""
    return OllamaClient()


@pytest.fixture(scope="function")
def clean_test_db():
    """テスト用DBのクリーンアップ"""
    test_paths = [
        "./data/test_chroma_db",
        "./data/test_char_db",
        "./data/test_integration_db",
        "./data/test_perf_db",
        "./data/test_startup_db",
    ]

    # テスト前クリーンアップ
    for path in test_paths:
        if os.path.exists(path):
            shutil.rmtree(path)

    yield

    # テスト後クリーンアップ
    for path in test_paths:
        if os.path.exists(path):
            shutil.rmtree(path)
