# core/rag_engine.py

import chromadb
from typing import List, Dict, Optional
import logging
import os
import time


class RAGEngine:
    """
    RAG検索エンジン

    easy-local-ragからの継承:
    - コサイン類似度検索
    - チャンク分割（1000文字）

    duo-talk用の改良:
    - ChromaDB永続化
    - メタデータフィルタリング
    - 関連度スコア返却
    """

    def __init__(
        self,
        ollama_client,
        chroma_path: str = "./data/chroma_db",
        collection_name: str = "duo_knowledge",
    ):
        """
        Args:
            ollama_client: OllamaClientインスタンス
            chroma_path: ChromaDB永続化パス
            collection_name: コレクション名
        """
        self.ollama = ollama_client
        self.chroma_path = chroma_path
        self.logger = logging.getLogger(__name__)

        # ChromaDB初期化
        os.makedirs(chroma_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=chroma_path)

        # コレクション取得or作成（コサイン類似度を使用）
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.logger.info(f"RAGEngine初期化完了: {self.collection.count()}件の知識")

    def add_knowledge(self, texts: List[str], metadatas: List[Dict[str, str]]):
        """
        知識追加

        Args:
            texts: テキストのリスト
            metadatas: メタデータのリスト
                例: {"domain": "technical", "character": "both"}
        """
        if len(texts) != len(metadatas):
            raise ValueError("texts と metadatas の長さが一致しません")

        # ID生成（タイムスタンプベース）
        base_id = int(time.time() * 1000)
        ids = [f"doc_{base_id}_{i}" for i in range(len(texts))]

        # 埋め込み生成
        embeddings = []
        for text in texts:
            emb = self.ollama.embed(text)
            embeddings.append(emb)

        # ChromaDBに追加
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        self.logger.info(f"{len(texts)}件の知識を追加")

    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        """
        類似度検索

        Args:
            query: 検索クエリ
            top_k: 取得件数
            filters: メタデータフィルタ
                例: {"character": "yana"}

        Returns:
            検索結果:
            [
                {
                    "text": "検索されたテキスト",
                    "score": 0.85,  # 類似度
                    "metadata": {"domain": "technical", ...}
                },
                ...
            ]
        """
        # 空のコレクションの場合は空リストを返す
        if self.collection.count() == 0:
            return []

        # クエリの埋め込み生成
        query_embedding = self.ollama.embed(query)

        # ChromaDBで検索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,  # メタデータフィルタ
        )

        # 結果整形
        formatted = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                formatted.append(
                    {
                        "text": results["documents"][0][i],
                        "score": 1 - results["distances"][0][i],  # 距離→類似度
                        "metadata": results["metadatas"][0][i],
                    }
                )

        self.logger.debug(f"検索: '{query}' → {len(formatted)}件")
        return formatted

    def init_from_files(
        self,
        knowledge_dir: str,
        metadata_mapping: Dict[str, Dict],
    ):
        """
        ファイルから知識ベース初期化

        Args:
            knowledge_dir: 知識ファイルディレクトリ
            metadata_mapping: ファイル名→メタデータ
                例:
                {
                    "jetracer_tech.txt": {
                        "domain": "technical",
                        "character": "both"
                    }
                }
        """
        # 既に知識があればスキップ
        if self.collection.count() > 0:
            self.logger.info("既存知識を使用")
            return

        self.logger.info("知識ベース初期化開始")

        for filename, metadata in metadata_mapping.items():
            filepath = os.path.join(knowledge_dir, filename)

            if not os.path.exists(filepath):
                self.logger.warning(f"ファイル未発見: {filepath}")
                continue

            # ファイル読み込み
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # チャンク分割
            chunks = self._chunk_text(content, max_chars=1000)

            # メタデータにソース追加
            metadatas = []
            for _ in chunks:
                meta = metadata.copy()
                meta["source"] = filename
                metadatas.append(meta)

            # 知識追加
            self.add_knowledge(chunks, metadatas)

        self.logger.info(f"初期化完了: {self.collection.count()}件の知識")

    def _chunk_text(self, text: str, max_chars: int = 1000) -> List[str]:
        """
        テキストをチャンク分割

        Args:
            text: 分割対象テキスト
            max_chars: 最大文字数

        Returns:
            チャンクのリスト

        Note:
            easy-local-ragと同じ方式（文単位で分割）
        """
        # 改行で分割
        lines = text.split("\n")

        chunks = []
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    # 単一行がmax_charsを超える場合は分割
                    chunks.append(line[:max_chars])
                    remaining = line[max_chars:]
                    while len(remaining) > max_chars:
                        chunks.append(remaining[:max_chars])
                        remaining = remaining[max_chars:]
                    if remaining:
                        current_chunk = remaining
            else:
                current_chunk += "\n" + line if current_chunk else line

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
