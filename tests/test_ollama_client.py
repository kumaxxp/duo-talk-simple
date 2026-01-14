# tests/test_ollama_client.py

import pytest
import time
from core.ollama_client import OllamaClient


class TestOllamaClient:
    """OllamaClient ユニットテスト（TDD方式）"""

    def test_init(self):
        """TC-O-001: 初期化テスト"""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434/v1"
        assert client.model == "gemma3:12b"
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_is_healthy(self):
        """TC-O-002: Ollama接続確認"""
        client = OllamaClient()
        assert client.is_healthy() is True

    def test_generate_basic(self):
        """TC-O-003: 基本的なテキスト生成"""
        client = OllamaClient()
        messages = [{"role": "user", "content": "こんにちは"}]
        response = client.generate(messages)

        assert isinstance(response, str)
        assert len(response) > 0
        assert len(response) < 5000  # 異常な長さでない

    def test_generate_with_params(self):
        """TC-O-004: パラメータ付き生成"""
        client = OllamaClient()
        messages = [{"role": "user", "content": "こんにちは"}]
        response = client.generate(
            messages,
            temperature=0.5,
            max_tokens=100
        )

        assert isinstance(response, str)
        assert len(response) > 0

    def test_embed_basic(self):
        """TC-O-005: 基本的な埋め込み生成"""
        client = OllamaClient()
        embedding = client.embed("JetRacerとは自律走行車です")

        assert isinstance(embedding, list)
        assert len(embedding) == 1024  # mxbai-embed-large
        assert all(isinstance(x, float) for x in embedding)

    def test_retry_mechanism(self):
        """TC-O-006: リトライ機構テスト"""
        # 無効なURLで接続失敗をシミュレート
        client = OllamaClient(
            base_url="http://invalid:11434/v1",
            max_retries=3
        )

        start_time = time.time()
        with pytest.raises(Exception):
            client.generate([{"role": "user", "content": "test"}])
        elapsed = time.time() - start_time

        # exponential backoff: 2^0 + 2^1 + 2^2 = 1 + 2 + 4 = 7秒以上
        assert elapsed > 7

    def test_timeout(self):
        """TC-O-007: タイムアウト設定確認"""
        # カスタムタイムアウトが正しく設定されることを確認
        client = OllamaClient(timeout=5.0)
        assert client.timeout == 5.0

        # 無効なURLに対して短いタイムアウトで接続失敗を確認
        client_short = OllamaClient(
            base_url="http://192.0.2.1:11434/v1",  # TEST-NET-1 (到達不能)
            timeout=0.5,
            max_retries=1,
        )

        start_time = time.time()
        with pytest.raises(Exception):
            client_short.generate([{"role": "user", "content": "test"}])
        elapsed = time.time() - start_time

        # タイムアウトが適用されていることを確認（5秒以内に終了）
        # 接続オーバーヘッドを考慮
        assert elapsed < 5.0
