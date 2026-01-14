# core/character.py

import yaml
from typing import List, Dict, Optional
import logging


class Character:
    """
    キャラクター応答生成

    easy-local-ragからの継承:
    - 会話履歴管理
    - システムプロンプト活用

    duo-talk用の追加:
    - キャラクター設定（YAML）
    - Query Rewrite（オプション）
    - RAG検索統合
    """

    def __init__(
        self,
        name: str,
        config_path: str,
        ollama_client,
        rag_engine,
    ):
        """
        Args:
            name: キャラクター名（"yana" | "ayu"）
            config_path: 設定ファイルパス（YAML）
            ollama_client: OllamaClientインスタンス
            rag_engine: RAGEngineインスタンス
        """
        self.name = name
        self.ollama = ollama_client
        self.rag = rag_engine
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # 設定読み込み
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # 会話履歴（最大10ターン）
        self.history: List[Dict[str, str]] = []
        self.max_history = 10

        # デバッグ用: 最後のRAG検索結果
        self.last_rag_results: List[Dict] = []

        self.logger.info(f"キャラクター初期化: {self.name}")

    def respond(
        self,
        user_input: str,
        use_rag: bool = True,
        rewrite_query: bool = False,
    ) -> str:
        """
        応答生成

        Args:
            user_input: ユーザー入力
            use_rag: RAG検索を使用するか
            rewrite_query: クエリ書き換えを使用するか

        Returns:
            応答テキスト
        """
        # 1. [オプション] Query Rewrite
        search_query = user_input
        if rewrite_query and len(self.history) > 0:
            search_query = self._rewrite_query(user_input)
            self.logger.debug(f"Query書き換え: {user_input} → {search_query}")

        # 2. RAG検索
        context = ""
        self.last_rag_results = []  # リセット
        if use_rag:
            rag_results = self.rag.search(
                query=search_query,
                top_k=3,
            )
            self.last_rag_results = rag_results  # 保存

            if rag_results:
                context_parts = [r["text"] for r in rag_results]
                context = "\n\n".join(context_parts)

        # 3. システムプロンプト構築
        system_prompt = self._build_system_prompt(context)

        # 4. メッセージ構築
        messages = [{"role": "system", "content": system_prompt}]

        # 会話履歴追加
        messages.extend(self.history)

        # ユーザー入力追加
        messages.append({"role": "user", "content": user_input})

        # 5. LLM生成
        temperature = self.config.get("generation", {}).get("temperature", 0.7)
        response = self.ollama.generate(
            messages=messages,
            temperature=temperature,
        )

        # 6. 履歴更新
        self._update_history(user_input, response)

        return response

    def _build_system_prompt(self, context: str) -> str:
        """
        システムプロンプト構築

        Args:
            context: RAG検索結果

        Returns:
            システムプロンプト
        """
        base_prompt = self.config["system_prompt"]

        if context:
            return f"""{base_prompt}

# 関連知識
以下の情報を参考にして応答してください：

{context}
"""
        return base_prompt

    def _rewrite_query(self, user_input: str) -> str:
        """
        クエリ書き換え（会話履歴を考慮）

        Args:
            user_input: 元のユーザー入力

        Returns:
            書き換え後のクエリ

        Note:
            easy-local-ragのQuery Rewrite機能を参考
        """
        # 直近2ターンを取得
        recent_history = (
            self.history[-4:] if len(self.history) >= 4 else self.history
        )

        context_str = ""
        for msg in recent_history:
            role = "ユーザー" if msg["role"] == "user" else "アシスタント"
            context_str += f"{role}: {msg['content']}\n"

        rewrite_prompt = f"""以下の会話履歴を踏まえて、ユーザーの最新の質問を具体的な検索クエリに書き換えてください。
代名詞や省略を解消し、検索に適した形にしてください。

会話履歴:
{context_str}

ユーザーの質問: {user_input}

書き換え後のクエリ（1文で簡潔に）:"""

        messages = [{"role": "user", "content": rewrite_prompt}]

        rewritten = self.ollama.generate(
            messages=messages,
            temperature=0.1,  # 安定性重視
        )

        return rewritten.strip()

    def _update_history(self, user_input: str, response: str):
        """
        会話履歴更新

        Args:
            user_input: ユーザー入力
            response: AI応答
        """
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        # 最大履歴数を超えたら古いものを削除
        while len(self.history) > self.max_history * 2:  # user+assistant=2
            self.history.pop(0)

    def clear_history(self):
        """会話履歴をクリア"""
        self.history = []
        self.logger.info("会話履歴をクリア")
