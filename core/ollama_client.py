# core/ollama_client.py

from openai import OpenAI
import ollama
import time
import logging
from typing import List, Dict


class OllamaClient:
    """
    Ollama接続クライアント

    easy-local-ragからの継承:
    - OpenAI互換APIの活用
    - ollama.embeddings()の直接利用

    duo-talk用の改良:
    - リトライ機構（exponential backoff）
    - タイムアウト処理
    - 詳細なエラーログ
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "gemma3:12b",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Args:
            base_url: Ollama API URL
            model: 使用するLLMモデル名
            timeout: タイムアウト時間（秒）
            max_retries: リトライ最大回数
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # OpenAI互換クライアント（LLM生成用）
        self.client = OpenAI(
            base_url=base_url,
            api_key="dummy",  # Ollamaはキー不要
            timeout=timeout,
        )

        self.logger = logging.getLogger(__name__)

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        テキスト生成（リトライ付き）

        Args:
            messages: OpenAI形式のメッセージ
                [
                    {"role": "system", "content": "..."},
                    {"role": "user", "content": "..."}
                ]
            temperature: 生成の多様性（0.0-2.0）
            max_tokens: 最大生成トークン数

        Returns:
            生成されたテキスト

        Raises:
            ConnectionError: 接続失敗
            TimeoutError: タイムアウト
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content

            except Exception as e:
                self.logger.warning(
                    f"生成失敗（試行 {attempt + 1}/{self.max_retries}）: {e}"
                )

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2**attempt
                    self.logger.info(f"{wait_time}秒待機後にリトライ")
                    time.sleep(wait_time)
                else:
                    self.logger.error("最大リトライ回数を超過")
                    raise

        # この行には到達しないが、型チェッカー用
        raise RuntimeError("Unexpected state in generate")

    def embed(self, text: str, model: str = "mxbai-embed-large") -> List[float]:
        """
        埋め込みベクトル生成

        Args:
            text: 埋め込み対象テキスト
            model: 埋め込みモデル名

        Returns:
            埋め込みベクトル（リスト形式）

        Note:
            easy-local-ragと同じollama.embeddings()を使用
        """
        try:
            response = ollama.embeddings(model=model, prompt=text)
            return response["embedding"]

        except Exception as e:
            self.logger.error(f"埋め込み生成失敗: {e}")
            raise

    def is_healthy(self) -> bool:
        """
        Ollama接続確認

        Returns:
            接続可能ならTrue
        """
        try:
            # シンプルなメッセージで確認
            self.generate(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except Exception:
            return False

    def set_model(self, model: str) -> None:
        """
        モデルを動的に切り替え

        Args:
            model: 新しいモデル名
        """
        self.model = model
        self.logger.info(f"モデルを変更: {model}")

    def get_model(self) -> str:
        """現在のモデル名を取得"""
        return self.model
