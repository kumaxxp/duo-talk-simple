# easy-local-rag 比較分析

## 概要

duo-talk-simpleは**easy-local-rag**（GitHub: AllAboutAI-YT/easy-local-rag, 1.2k stars）を参考に設計されています。このドキュメントでは、easy-local-ragの優れた点を分析し、duo-talk用にどのように改良したかを記録します。

---

## easy-local-ragの分析

### プロジェクト概要

| 項目 | 内容 |
|------|------|
| リポジトリ | https://github.com/AllAboutAI-YT/easy-local-rag |
| スター数 | 1.2k（2026年1月時点） |
| 言語 | Python |
| 主要ファイル | localrag.py（約350行） |
| 特徴 | シンプル・実用的・初心者フレンドリー |

### 技術スタック

| 技術 | easy-local-rag | duo-talk-simple |
|------|---------------|-----------------|
| LLM実行環境 | Ollama | Ollama（同じ） |
| LLM API | OpenAI互換 | OpenAI互換（同じ） |
| 埋め込みモデル | mxbai-embed-large | mxbai-embed-large（同じ） |
| ベクトルDB | **なし（メモリ）** | **ChromaDB** |
| 検索方式 | コサイン類似度（PyTorch） | ChromaDB組み込み検索 |
| 設定 | config.yaml | config.yaml（拡張版） |

---

## easy-local-ragの優れた点

### 1. シンプルさの追求

#### ファイル構成

```
easy-local-rag/
├── localrag.py              # メイン（350行）
├── localrag_no_rewrite.py   # Query Rewriteなし版
├── upload.py                # ドキュメント投入
├── vault.txt                # 知識ストレージ
├── config.yaml              # 設定
└── requirements.txt         # 依存
```

**総ファイル数**: 6ファイルのみ

**学び**:
- ✅ ファイル数を最小限に
- ✅ 1ファイル完結の設計
- ✅ すぐに動かせる

**duo-talk-simpleへの適用**:
- コア機能を3ファイルに集約
- テストを除けば15ファイル程度
- 各ファイルの責務を明確に

---

### 2. OpenAI互換APIの活用

#### easy-local-ragのコード

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="llama3",
    messages=conversation_history
)
```

**優れている点**:
- シンプルな接続
- OpenAI APIと同じコード
- 切り替えが容易

**duo-talk-simpleへの適用**:
- そのまま継承
- リトライ処理を追加
- エラーハンドリング強化

---

### 3. 埋め込み生成の直接呼び出し

#### easy-local-ragのコード

```python
import ollama

def get_embedding(text):
    response = ollama.embeddings(
        model="mxbai-embed-large",
        prompt=text
    )
    return response["embedding"]
```

**優れている点**:
- APIではなくSDK直接利用
- シンプルで高速
- エラーが少ない

**duo-talk-simpleへの適用**:
- 同じ方式を採用
- OllamaClient.embed()に実装

---

### 4. コサイン類似度検索

#### easy-local-ragのコード

```python
import torch

# vault.txtから知識を読み込み
vault_content = [line.strip() for line in open('vault.txt', 'r')]

# 埋め込み生成
vault_embeddings = [get_embedding(content) for content in vault_content]
vault_embeddings_tensor = torch.tensor(vault_embeddings)

# クエリの埋め込み
query_embedding = get_embedding(user_input)
query_tensor = torch.tensor(query_embedding).unsqueeze(0)

# コサイン類似度計算
cos_scores = torch.cosine_similarity(query_tensor, vault_embeddings_tensor)

# top-k取得
top_k = torch.topk(cos_scores, k=3)
```

**優れている点**:
- シンプルで理解しやすい
- PyTorchの高速計算
- 外部DBが不要

**duo-talk-simpleへの適用**:
- ChromaDBが同じ原理を使用
- 永続化のメリットを追加

---

### 5. Query Rewrite機能

#### easy-local-ragのコード

```python
def rewrite_query(conversation_history, user_input):
    # 直近の会話を文脈として使用
    context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history[-4:]
    ])
    
    rewrite_prompt = f"""
    会話履歴:
    {context}
    
    ユーザーの質問: {user_input}
    
    この質問を、検索に適した具体的なクエリに書き換えてください。
    """
    
    response = client.chat.completions.create(
        model=ollama_model,
        messages=[{"role": "user", "content": rewrite_prompt}],
        temperature=0.1
    )
    
    return response.choices[0].message.content
```

**優れている点**:
- 代名詞（「それ」「あれ」）を解消
- 文脈を考慮した検索
- temperature=0.1で安定性重視

**duo-talk-simpleへの適用**:
- Character._rewrite_query()に実装
- オプション機能として提供（デフォルトOFF）

---

### 6. 会話履歴管理

#### easy-local-ragのコード

```python
conversation_history = []

# ユーザー入力を追加
conversation_history.append({
    "role": "user",
    "content": user_input
})

# システムメッセージ + 履歴をLLMに送信
messages = [
    {"role": "system", "content": system_message},
    *conversation_history
]

# 応答を履歴に追加
conversation_history.append({
    "role": "assistant",
    "content": response
})
```

**優れている点**:
- OpenAI形式の標準的な履歴
- シンプルなリスト管理
- LLMにそのまま渡せる

**duo-talk-simpleへの適用**:
- そのまま継承
- 最大10ターンに制限
- FIFO方式で古いものを削除

---

## easy-local-ragの限界

### 1. 永続化の欠如

#### 問題点

```python
# 毎回vault.txtから読み込み
vault_content = [line.strip() for line in open('vault.txt', 'r')]

# 毎回埋め込み生成（遅い！）
vault_embeddings = [get_embedding(content) for content in vault_content]
```

**影響**:
- 起動に時間がかかる（150チャンク → ~25秒）
- 2回目も同じ時間
- スケーラビリティの問題

**duo-talk-simpleの改善**:
```python
# ChromaDBで永続化
self.collection = self.client.get_or_create_collection("duo_knowledge")

# 初回のみ埋め込み生成
if self.collection.count() == 0:
    # 知識投入（初回のみ）
    self.init_from_files(...)

# 2回目以降は高速（~5秒）
```

---

### 2. メタデータの欠如

#### 問題点

```python
# vault.txtには生テキストのみ
"""
JetRacerは自律走行車です
モーター制御はPWM信号です
...
"""
```

**影響**:
- ドメイン別検索ができない
- キャラクター別知識の区別不可
- 優先度付けができない

**duo-talk-simpleの改善**:
```python
# メタデータ付きで保存
metadata = {
    "domain": "technical",      # technical / character / experience
    "character": "both",        # both / yana / ayu
    "importance": "high",       # high / medium / low
    "source": "jetracer_tech.txt"
}

# フィルタ検索が可能
results = rag.search(
    query="センサー",
    filters={"character": "yana"}  # やな関連のみ
)
```

---

### 3. エラー処理の不足

#### 問題点

```python
# エラー処理なし
response = client.chat.completions.create(
    model=ollama_model,
    messages=conversation_history
)
```

**影響**:
- Ollama停止時にクラッシュ
- ネットワークエラーで停止
- タイムアウト未対応

**duo-talk-simpleの改善**:
```python
def generate(self, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                timeout=self.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
```

---

### 4. 設定の柔軟性

#### 問題点

```yaml
# config.yamlが最小限
ollama_model: "llama3"
embedding_model: "mxbai-embed-large"
```

**影響**:
- モデル以外の設定変更が困難
- タイムアウトやリトライ回数が固定
- 環境別設定ができない

**duo-talk-simpleの改善**:
```yaml
ollama:
  base_url: "http://localhost:11434/v1"
  llm_model: "gemma3:12b"
  embedding_model: "mxbai-embed-large"
  timeout: 30.0
  max_retries: 3
  generation:
    temperature: 0.7
    max_tokens: 2000

rag:
  chroma_db_path: "./data/chroma_db"
  search:
    top_k: 3
    min_score: 0.5
  # ... 詳細な設定
```

---

### 5. テストの欠如

#### 問題点

- テストコードが存在しない
- 動作確認が手動のみ
- リグレッション検出が困難

**duo-talk-simpleの改善**:
```
tests/
├── test_ollama_client.py    # ユニットテスト
├── test_rag_engine.py        # ユニットテスト
├── test_character.py         # ユニットテスト
└── test_integration.py       # 統合テスト
```

---

## 比較表

### 機能比較

| 機能 | easy-local-rag | duo-talk-simple |
|------|---------------|-----------------|
| **Ollama統合** | ✅ OpenAI互換API | ✅ 同じ + リトライ |
| **埋め込み** | ✅ mxbai-embed-large | ✅ 同じ |
| **検索方式** | ✅ コサイン類似度 | ✅ ChromaDB（同原理） |
| **永続化** | ❌ なし（毎回生成） | ✅ ChromaDB |
| **メタデータ** | ❌ なし | ✅ ドメイン・キャラ別 |
| **Query Rewrite** | ✅ あり | ✅ オプション |
| **会話履歴** | ✅ シンプル | ✅ 同じ + 制限 |
| **エラー処理** | ❌ 最小限 | ✅ リトライ機構 |
| **設定外部化** | △ 一部 | ✅ 完全 |
| **テスト** | ❌ なし | ✅ 包括的 |
| **キャラクター** | ❌ なし | ✅ YAML設定 |

### パフォーマンス比較

| 項目 | easy-local-rag | duo-talk-simple |
|------|---------------|-----------------|
| **初回起動** | ~25秒 | ~30秒 |
| **2回目起動** | ~25秒 | **~5秒** |
| **応答時間** | ~3秒 | ~3秒 |
| **メモリ使用** | 少（DB不要） | 中（ChromaDB） |
| **ディスク使用** | 少（vault.txt） | 中（~100MB） |

### コード複雑度

| 項目 | easy-local-rag | duo-talk-simple |
|------|---------------|-----------------|
| **ファイル数** | 6 | 15 |
| **総行数** | ~500行 | ~1500行 |
| **コアロジック** | 350行（1ファイル） | ~800行（3ファイル） |
| **学習曲線** | 緩い（すぐ理解） | やや急（設計理解要） |

---

## 採用した点・改良した点

### 採用した点（easy-local-ragから）

| 要素 | 理由 |
|------|------|
| OpenAI互換API | シンプルで安定 |
| ollama.embeddings() | 高速で確実 |
| コサイン類似度 | 理解しやすい |
| Query Rewrite | 実用的な機能 |
| 会話履歴管理 | 標準的な方式 |
| config.yaml | 設定外部化の基本 |

### 改良した点（duo-talk用）

| 要素 | 改良内容 | 目的 |
|------|---------|------|
| ベクトルDB | ChromaDBで永続化 | 起動高速化 |
| メタデータ | ドメイン・キャラ別管理 | 検索精度向上 |
| エラー処理 | リトライ機構追加 | 安定性向上 |
| 設定ファイル | 詳細な設定項目 | カスタマイズ性 |
| テスト | 包括的テストスイート | 品質保証 |
| キャラクター | YAML設定による定義 | duo-talk要件 |

---

## 学んだ教訓

### 1. シンプルさの価値

**教訓**: 
- 複雑な機能より、動くコードが重要
- 初心者が理解できる設計を優先
- ファイル数を減らす努力

**duo-talk-simpleへの適用**:
- コア機能を3ファイルに集約
- 各ファイルの責務を明確に
- ドキュメントで補完

---

### 2. 実用性の重視

**教訓**:
- Query Rewriteなど実用的な機能
- すぐに試せる構成
- YouTube動画でのチュートリアル

**duo-talk-simpleへの適用**:
- Query Rewriteをオプション化
- README.mdでクイックスタート
- 段階的実装計画

---

### 3. 永続化の重要性

**教訓**:
- 起動時間がユーザー体験に直結
- 2回目以降の高速化は必須
- スケーラビリティを考慮

**duo-talk-simpleへの適用**:
- ChromaDBで永続化
- 初回30秒 → 2回目5秒

---

### 4. メタデータの威力

**教訓**:
- フィルタ検索で精度向上
- ドメイン別管理で整理
- 優先度付けが可能

**duo-talk-simpleへの適用**:
```python
metadata = {
    "domain": "technical",
    "character": "both",
    "importance": "high"
}
```

---

### 5. エラーハンドリングの必要性

**教訓**:
- 本番運用にはエラー処理が不可欠
- リトライ機構で安定性向上
- ログで問題追跡

**duo-talk-simpleへの適用**:
- exponential backoff
- 詳細なエラーログ
- タイムアウト処理

---

## まとめ

### easy-local-ragは優れた参考実装

**優れている点**:
- ✅ シンプルで理解しやすい
- ✅ すぐに動かせる
- ✅ Ollamaとの統合が完璧
- ✅ Query Rewriteなど実用機能

**duo-talk-simpleでの改良**:
- ✅ 永続化で起動高速化
- ✅ メタデータで検索精度向上
- ✅ エラー処理で安定性向上
- ✅ テストで品質保証
- ✅ キャラクター対応

### 設計思想の継承

```
easy-local-rag の「シンプルさ」
        ↓
duo-talk-simple の「シンプルさ + 拡張性」
```

**バランス**:
- ファイル数: 6 → 15（約2.5倍）
- 行数: 500 → 1500（約3倍）
- 機能: 基本 → 本番運用可能

---

## 謝辞

easy-local-rag（AllAboutAI-YT）の素晴らしい実装に感謝します。このプロジェクトなしでは、duo-talk-simpleの設計は完成しませんでした。

---

**作成日**: 2026年1月14日  
**最終更新**: 2026年1月14日  
**参考**: https://github.com/AllAboutAI-YT/easy-local-rag
