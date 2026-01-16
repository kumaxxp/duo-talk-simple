# core/character.py

import logging
from typing import Dict, List, Optional

from core import prompt_builder


class Character:
    """
    キャラクター応答生成器。
    - persona YAML (SSOT) + few-shot パターンから system prompt を構築
    - RAG結果を state/Deep Values に合成
    - 会話履歴とQuery Rewriteの器
    """

    def __init__(
        self,
        name: str,
        config_path: str,
        ollama_client,
        rag_engine,
        generation_defaults: Optional[Dict] = None,
        assets: Optional[Dict[str, str]] = None,
        max_history: int = 10,
    ):
        """
        Args:
            name: キャラクター名（"yana" | "ayu"）
            config_path: persona YAML path（SSOT）
            ollama_client: OllamaClient
            rag_engine: RAGEngine
            generation_defaults: config.yaml 側の generation 設定
            assets: few-shot や director などの共有パス
            max_history: 保存するターン数
        """
        self.name = name
        self.ollama = ollama_client
        self.rag = rag_engine
        self.logger = logging.getLogger(f"{__name__}.{name}")

        self.persona = prompt_builder.load_persona(config_path)
        self.assets = assets or {}
        self.few_shot_patterns = []

        patterns_path = self.assets.get("few_shot_patterns")
        if patterns_path:
            try:
                self.few_shot_patterns = prompt_builder.load_few_shot_patterns(patterns_path)
            except FileNotFoundError:
                self.logger.warning("Few-shot pattern file not found: %s", patterns_path)

        self.generation_defaults = generation_defaults or {}

        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.last_rag_results: List[Dict] = []
        self.current_state: Optional[str] = None

        self.logger.info("キャラクター初期化: %s", self.name)

    def respond(
        self,
        user_input: str,
        use_rag: bool = True,
        rewrite_query: bool = False,
    ) -> str:
        """
        応答生成。
        Args:
            user_input: ユーザ入力
            use_rag: RAG検索を使用するか
            rewrite_query: Query Rewriteを使うか
        """
        search_query = user_input
        if rewrite_query and self.history:
            search_query = self._rewrite_query(user_input)
            self.logger.debug("Query書き換え %s -> %s", user_input, search_query)

        context = ""
        self.last_rag_results = []
        if use_rag:
            rag_results = self.rag.search(query=search_query, top_k=3)
            self.last_rag_results = rag_results
            if rag_results:
                context = "\n\n".join(r["text"] for r in rag_results)

        system_prompt, gen_overrides = self._build_system_prompt(context, user_input)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_input})

        temperature = gen_overrides.get(
            "temperature",
            self.generation_defaults.get("temperature", 0.7),
        )
        max_tokens = self.generation_defaults.get("max_tokens", 2000)

        response = self.ollama.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self._update_history(user_input, response)
        return response

    def _build_system_prompt(self, context: str, user_input: str):
        """persona + state + RAGから system prompt を生成。"""

        state = prompt_builder.guess_state(self.persona, user_input)
        if state not in self.persona.state_controls:
            fallback = self.persona.required_states[0] if self.persona.required_states else "focused"
            self.logger.debug("state %s 未定義のため %s にフォールバック", state, fallback)
            state = fallback

        few_shot = prompt_builder.select_few_shot(self.few_shot_patterns, self.persona.id, state)
        rag_block = context if context else None

        prompt, gen_overrides = prompt_builder.build_system_prompt(
            persona=self.persona,
            state=state,
            few_shot=few_shot,
            rag=rag_block,
        )
        self.current_state = state
        return prompt, gen_overrides

    def _rewrite_query(self, user_input: str) -> str:
        """
        クエリ書き換え（会話履歴を使用）。
        easy-local-ragのQuery Rewrite機構を参考。
        """

        recent_history = self.history[-4:] if len(self.history) >= 4 else self.history
        context_str = ""
        for msg in recent_history:
            role = "ユーザー" if msg["role"] == "user" else "アシスタント"
            context_str += f"{role}: {msg['content']}\n"

        rewrite_prompt = f"""以下の会話と最新質問を踏まえて検索クエリを構築してください。
会話履歴:
{context_str}

ユーザーの質問: {user_input}

書き換え後のクエリ（簡潔に1行）:"""

        messages = [{"role": "user", "content": rewrite_prompt}]
        rewritten = self.ollama.generate(messages=messages, temperature=0.1, max_tokens=128)
        return rewritten.strip()

    def _update_history(self, user_input: str, response: str):
        """会話履歴を追加し、最大保持数を超えたら古いものから削除。"""

        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        while len(self.history) > self.max_history * 2:
            self.history.pop(0)

    def clear_history(self):
        """会話履歴をクリア。"""

        self.history = []
        self.current_state = None
        self.logger.info("会話履歴をクリア")
