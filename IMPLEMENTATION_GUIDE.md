# duo-talk-simple 実装指示書（Claude Code用）

**プロジェクト**: duo-talk-simple  
**開発方針**: テスト駆動開発（TDD）  
**目標**: Phase 0 → Phase 5まで完成

---

## 作業環境

**作業マシン**: Windows 11 / RTX 1660 Ti  
**作業ディレクトリ**: `C:\work\duo-talk-simple`  
**Python**: 3.10以上  
**開発方針**: **Red → Green → Refactor**

---

## 📚 参照ドキュメント（必読）

実装前に必ず以下のドキュメントを確認してください：

| ドキュメント | 用途 |
|------------|------|
| `docs/01_アーキテクチャ設計.md` | システム全体構成・レイヤー構造 |
| `docs/02_コンポーネント詳細.md` | クラス設計・API仕様 |
| `docs/05_実装計画.md` | TDDサイクル・Phase定義 |
| `docs/06_テスト戦略.md` | テストケース一覧・品質基準 |
| `docs/07_実装サンプル.md` | 実装コード例 |
| `docs/08_設計レビュー報告書.md` | 設計レビュー結果 |
| `config.yaml` | システム設定値 |
| `personas/yana.yaml` | やなのペルソナ定義 |
| `personas/ayu.yaml` | あゆのペルソナ定義 |

---

## 🎯 TDD開発フロー（厳守）

### 基本サイクル

```
1. RED（失敗）
   - テストコードを書く
   - pytest実行 → 失敗確認
   
2. GREEN（成功）
   - 最小限の実装を書く
   - pytest実行 → 成功確認
   
3. REFACTOR（改善）
   - コードを整理・最適化
   - pytest実行 → 成功維持確認
   
4. 次のテストへ
```

### 重要原則

⚠️ **テストファースト厳守**: 実装前に必ずテストを書く  
⚠️ **最小実装**: テストを通す最小限のコードのみ  
⚠️ **リファクタリング**: テスト成功を維持しながら改善  

---

## 📋 Phase 0: 環境準備

**目標**: 開発環境とテスト基盤の構築

### タスク 0.1: ディレクトリ作成

```bash
# Windows PowerShellで実行
cd C:\work\duo-talk-simple

# ディレクトリ作成
New-Item -ItemType Directory -Path core, tests, data, logs -Force

# __init__.py作成
New-Item -ItemType File -Path core\__init__.py -Force
New-Item -ItemType File -Path tests\__init__.py -Force
```

**確認**:
```bash
tree /F  # ディレクトリ構造確認
```

### タスク 0.2: requirements.txt作成

**ファイル**: `requirements.txt`

```txt
# LLM
openai>=1.0.0

# Ollama (ローカルで別途インストール必要)
# ollama>=0.4.4

# RAG
chromadb>=0.4.22

# Configuration
pyyaml>=6.0
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0

# Development
black>=23.0.0
flake8>=6.0.0
```

**実行**:
```bash
pip install -r requirements.txt
```

### タスク 0.3: pytest.ini作成

**ファイル**: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v
    --strict-markers
    --disable-warnings
    --cov=core
    --cov-report=term-missing
    --cov-report=html
    --tb=short

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
```

### タスク 0.4: Ollama動作確認

```bash
# Ollama起動確認
ollama --version

# モデルダウンロード（まだの場合）
ollama pull gemma3:12b
ollama pull mxbai-embed-large

# 動作テスト
ollama run gemma3:12b
# プロンプト: "こんにちは"
# 応答があればOK
```

### タスク 0.5: pytest動作確認

```bash
# pytest動作確認（まだテストはないが、実行できることを確認）
pytest --version
pytest tests/ -v
# "no tests ran" と表示されればOK
```

### Phase 0 完了基準

- [x] ディレクトリ構成完成
- [x] requirements.txt作成
- [x] pytest.ini作成
- [x] Ollama起動確認
- [x] gemma3:12b実行可能
- [x] mxbai-embed-large実行可能
- [x] pytest動作確認

---

## 📋 Phase 1: OllamaClient（TDD）

**参照**: `docs/05_実装計画.md` Phase 1セクション

### Step 1.1: テストケース作成（RED）

**ファイル**: `tests/test_ollama_client.py`

**参照**: `docs/07_実装サンプル.md` 6.1 OllamaClient テスト完全版

**実装内容**:
```python
# tests/test_ollama_client.py
import pytest
from core.ollama_client import OllamaClient

class TestOllamaClient:
    def test_init(self):
        """TC-O-001: 初期化テスト"""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434/v1"
        assert client.model == "gemma3:12b"
    
    # 以下、docs/07_実装サンプル.md の通りに実装
```

**実行（失敗確認）**:
```bash
pytest tests/test_ollama_client.py -v
# → ModuleNotFoundError: No module named 'core.ollama_client'
```

### Step 1.2: 最小実装（GREEN）

**ファイル**: `core/ollama_client.py`

**参照**: `docs/07_実装サンプル.md` 1.1 完全実装例

**実装内容**:
```python
# core/ollama_client.py
from openai import OpenAI
import ollama
from typing import List, Dict

class OllamaClient:
    def __init__(self, 
                 base_url: str = "http://localhost:11434/v1",
                 model: str = "gemma3:12b"):
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key="dummy")
    
    # 以下、docs/07_実装サンプル.md の通りに実装
```

**実行（成功確認）**:
```bash
pytest tests/test_ollama_client.py::TestOllamaClient::test_init -v
# → 1 passed
```

### Step 1.3: 追加テスト → 実装（繰り返し）

1. `test_is_healthy()` 追加 → 実装
2. `test_generate_basic()` 追加 → 実装
3. `test_generate_with_params()` 追加 → 実装
4. `test_embed_basic()` 追加 → 実装
5. `test_retry_mechanism()` 追加 → 実装
6. `test_timeout()` 追加 → 実装

**各ステップで**:
```bash
# テスト追加
pytest tests/test_ollama_client.py -v
# → 失敗確認

# 実装
# （コード追加）

# テスト実行
pytest tests/test_ollama_client.py -v
# → 成功確認
```

### Step 1.4: リファクタリング（REFACTOR）

- ログ追加
- エラーハンドリング改善
- exponential backoff実装

**実行（成功維持確認）**:
```bash
pytest tests/test_ollama_client.py -v
# → 全て成功
```

### Phase 1 完了基準

- [x] 全テスト成功（7件）
- [x] カバレッジ > 80%
- [x] Ollama接続動作確認
- [x] リトライ機構動作確認

```bash
# カバレッジ確認
pytest tests/test_ollama_client.py --cov=core.ollama_client --cov-report=term-missing
```

---

## 📋 Phase 2: RAGEngine（TDD）

**参照**: `docs/05_実装計画.md` Phase 2セクション

### Step 2.1: テストケース作成（RED）

**ファイル**: `tests/test_rag_engine.py`

**参照**: `docs/07_実装サンプル.md` 6.2 RAGEngine テスト完全版

**実装内容**:
```python
# tests/test_rag_engine.py
import pytest
import shutil
import os
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine

@pytest.fixture
def rag_engine():
    """テスト用RAGEngine"""
    # ... (docs/07_実装サンプル.md 参照)
```

**実行（失敗確認）**:
```bash
pytest tests/test_rag_engine.py -v
# → ModuleNotFoundError
```

### Step 2.2: 最小実装（GREEN）

**ファイル**: `core/rag_engine.py`

**参照**: `docs/07_実装サンプル.md` 2.1 完全実装例

**実装内容**:
```python
# core/rag_engine.py
import chromadb
from typing import List, Dict, Optional

class RAGEngine:
    def __init__(self, ollama_client, chroma_path: str = "./data/chroma_db"):
        # ... (docs/07_実装サンプル.md 参照)
```

**実行（成功確認）**:
```bash
pytest tests/test_rag_engine.py::TestRAGEngine::test_init -v
# → 1 passed
```

### Step 2.3: 追加テスト → 実装（繰り返し）

1. `test_add_knowledge()` 追加 → 実装
2. `test_search_basic()` 追加 → 実装
3. `test_search_with_filter()` 追加 → 実装
4. `test_search_accuracy()` 追加 → 実装
5. `test_chunk_text()` 追加 → 実装
6. `test_init_from_files()` 追加 → 実装
7. `test_empty_search()` 追加 → 実装

### Step 2.4: 知識ファイル投入テスト

**ファイル**: `knowledge/jetracer_tech.txt`（既に存在）  
**ファイル**: `knowledge/sisters_shared.txt`（既に存在）

**テスト**:
```python
def test_init_from_files(rag_engine):
    metadata_mapping = {
        "jetracer_tech.txt": {
            "domain": "technical",
            "character": "both"
        },
        "sisters_shared.txt": {
            "domain": "character",
            "character": "both"
        }
    }
    rag_engine.init_from_files("./knowledge", metadata_mapping)
    assert rag_engine.collection.count() > 0
```

### Phase 2 完了基準

- [x] 全テスト成功（8件）
- [x] カバレッジ > 80%
- [x] ChromaDB永続化確認
- [x] 検索精度確認（score > 0.5）
- [x] 知識ファイル投入成功

---

## 📋 Phase 3: Character（TDD）

**参照**: `docs/05_実装計画.md` Phase 3セクション

### Step 3.1: テストケース作成（RED）

**ファイル**: `tests/test_character.py`

**参照**: `docs/07_実装サンプル.md` 6.3 Character テスト完全版

### Step 3.2: 最小実装（GREEN）

**ファイル**: `core/character.py`

**参照**: `docs/07_実装サンプル.md` 3.1 完全実装例

**重要**: ペルソナYAML読み込み処理

```python
import yaml

def load_persona(persona_path: str) -> Dict:
    with open(persona_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
```

### Step 3.3: 追加テスト → 実装（繰り返し）

1. `test_init()` 追加 → 実装
2. `test_respond_basic()` 追加 → 実装
3. `test_respond_with_rag()` 追加 → 実装
4. `test_history_management()` 追加 → 実装
5. `test_clear_history()` 追加 → 実装
6. `test_query_rewrite()` 追加 → 実装
7. `test_max_history_limit()` 追加 → 実装

### Step 3.4: キャラクター性の確認（手動テスト）

```python
# 手動テスト用スクリプト
client = OllamaClient()
rag = RAGEngine(client, chroma_path="./data/chroma_db")
yana = Character("yana", "./personas/yana.yaml", client, rag)

# やなの口調確認
response = yana.respond("こんにちは")
print(response)
# → 「やっほー！」のようなカジュアルな挨拶

# あゆの口調確認
ayu = Character("ayu", "./personas/ayu.yaml", client, rag)
response = ayu.respond("こんにちは")
print(response)
# → 「こんにちは。姉様と...」のような丁寧な挨拶
```

### Phase 3 完了基準

- [x] 全テスト成功（7件）
- [x] やな・あゆの口調確認
- [x] RAG統合動作確認
- [x] 履歴管理確認
- [x] **手動確認**: やなは丁寧語を使わない
- [x] **手動確認**: あゆは姉を「姉様」と呼ぶ

---

## 📋 Phase 4: 統合（TDD）

**参照**: `docs/05_実装計画.md` Phase 4セクション

### Step 4.1: 統合テスト作成（RED）

**ファイル**: `tests/test_integration.py`

**参照**: `docs/07_実装サンプル.md` 6.4 統合テスト完全版

### Step 4.2: chat.py実装

**ファイル**: `chat.py`

**参照**: `docs/07_実装サンプル.md` 5.1 Application完全実装

**実装内容**:
```python
# chat.py
import yaml
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine
from core.character import Character

def main():
    # config.yaml読み込み
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # 初期化
    client = OllamaClient(
        base_url=config["ollama"]["base_url"],
        model=config["ollama"]["llm_model"]
    )
    
    # ... (docs/07_実装サンプル.md 参照)

if __name__ == "__main__":
    main()
```

### Step 4.3: 実行確認

```bash
python chat.py
```

**期待される動作**:
1. 起動メッセージ表示
2. キャラクター選択（yana/ayu）
3. 会話ループ
4. コマンド動作（/switch, /clear, /exit）

### Phase 4 完了基準

- [x] 統合テスト全成功（5件）
- [x] chat.py起動成功
- [x] やな・あゆ切り替え動作
- [x] コマンド動作（/clear, /exit, /switch）
- [x] RAG統合動作確認

---

## 📋 Phase 5: 品質向上とCI/CD

**参照**: `docs/05_実装計画.md` Phase 5セクション

### Step 5.1: カバレッジ確認

```bash
pytest tests/ --cov=core --cov-report=html
# htmlcov/index.html を開いてカバレッジ確認
```

**目標**: カバレッジ > 80%

### Step 5.2: パフォーマンステスト追加

**ファイル**: `tests/test_performance.py`

**参照**: `docs/07_実装サンプル.md` 6.5 パフォーマンステスト完全版

**実装内容**:
```python
# tests/test_performance.py
import pytest
import time

class TestPerformance:
    def test_response_time(self):
        """TC-P-001: 応答時間テスト"""
        # ... (docs/07_実装サンプル.md 参照)
```

### Step 5.3: README.md作成

**ファイル**: `README.md`

```markdown
# duo-talk-simple

やなとあゆがJetRacerについてお話しします。

## 特徴
- TDD方式で実装
- Ollama + Gemma3使用
- RAG（検索拡張生成）対応
- 姉妹AIキャラクター

## セットアップ

### 1. Ollama インストール
https://ollama.com/

### 2. モデルダウンロード
```bash
ollama pull gemma3:12b
ollama pull mxbai-embed-large
```

### 3. 依存ライブラリ
```bash
pip install -r requirements.txt
```

## 実行

```bash
python chat.py
```

## テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ確認
pytest tests/ --cov=core --cov-report=html
```

## プロジェクト構成

```
duo-talk-simple/
├── chat.py              # メインアプリケーション
├── config.yaml          # システム設定
├── core/               # コアモジュール
│   ├── ollama_client.py
│   ├── rag_engine.py
│   └── character.py
├── personas/           # キャラクター設定
│   ├── yana.yaml
│   └── ayu.yaml
├── knowledge/          # 知識ベース
│   ├── jetracer_tech.txt
│   └── sisters_shared.txt
├── tests/              # テストコード
└── docs/               # 設計書
```

## ライセンス
MIT
```

### Phase 5 完了基準

- [x] カバレッジ > 80%
- [x] 全テスト成功
- [x] パフォーマンステスト合格
- [x] README.md作成
- [x] ドキュメント整合性確認

---

## 🎯 全体完成基準

### 必須条件

- [x] Phase 0-5 全て完了
- [x] 全テスト成功（100%）
- [x] カバレッジ > 80%
- [x] chat.py動作確認
- [x] やな・あゆのキャラクター性確認

### 品質指標

- [x] 応答時間 < 5秒
- [x] 初回起動 < 30秒
- [x] RAG検索 < 0.5秒
- [x] VRAM使用量 < 12GB

### ドキュメント

- [x] README.md作成
- [x] 全テストにdocstring
- [x] 設計書との整合性確認

---

## 📝 報告テンプレート

各Phase完了時に以下を報告してください：

```
## Phase X 完了報告

### 実施内容
- [ ] テストコード作成（件数）
- [ ] 実装コード作成
- [ ] テスト成功確認

### テスト結果
- 成功: X件
- 失敗: 0件
- カバレッジ: XX%

### 確認事項
- [ ] 設計書との整合性
- [ ] コーディング規約遵守
- [ ] 動作確認

### 次のPhase
Phase X+1に進みます
```

---

## ⚠️ トラブルシューティング

### Ollama接続失敗

```bash
# Ollamaが起動しているか確認
ollama ps

# 再起動
# Windowsの場合、タスクマネージャーからOllamaを再起動
```

### ChromaDB エラー

```bash
# データベース削除して再作成
Remove-Item -Recurse -Force ./data/chroma_db
```

### テスト失敗

```bash
# 特定のテストのみ実行
pytest tests/test_ollama_client.py::TestOllamaClient::test_init -v

# デバッガ起動
pytest tests/test_ollama_client.py --pdb
```

---

## 🚀 実装開始

**最初のコマンド**:
```bash
cd C:\work\duo-talk-simple
python -m pytest --version
```

**Phase 0から順番に実装してください。各Phaseの完了基準を満たしてから次へ進んでください。**

---

**作成日**: 2026年1月14日  
**対象**: Claude Code  
**プロジェクト**: duo-talk-simple  
**開発方針**: TDD（Test-Driven Development）
