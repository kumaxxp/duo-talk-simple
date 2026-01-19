# duo-talk-simple

TDD方式で実装した、姉妹AIによるJetRacer対話システム

## 概要

「やな」と「あゆ」という二人の姉妹AIが、JetRacer（自律走行車）についてお話しします。

- **やな（姉）**: 直感的・行動派、カジュアルな口調
- **あゆ（妹）**: 分析的・慎重派、丁寧な口調（ツッコミ役）

## 必要環境

- Python 3.12+
- Ollama（ローカルLLM）
- 推奨VRAM: 12GB以上

### Ollamaモデル

```bash
# 必須モデル
ollama pull gemma3:12b        # デフォルトLLM
ollama pull mxbai-embed-large # 埋め込み

# オプション（モデル比較用）
ollama pull hf.co/mmnga/tokyotech-llm-Llama-3.1-Swallow-8B-Instruct-v0.3-gguf:Q4_K_M  # Swallow
# Cydonia は別途インストール
```

## セットアップ

```bash
# 仮想環境作成
python3 -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# Ollama起動確認
ollama list
```

## 使い方

### 対話開始

```bash
python chat.py
```

### コマンド一覧

| コマンド | 説明 |
|----------|------|
| `/switch` | キャラクター切り替え |
| `/model` | モデル切り替え（gemma/swallow/cydonia） |
| `/duo <お題>` | AI姉妹対話モード |
| `/clear` | 会話履歴クリア |
| `/status` | 状態表示 |
| `/debug` | RAGデバッグ表示切替 |
| `/help` | ヘルプ表示 |
| `/exit` | 終了（ログ保存） |

### モデルプリセット

| プリセット | モデル | VRAM | 特徴 |
|-----------|--------|------|------|
| `gemma` | gemma3:12b | 8.1GB | バランス型（デフォルト） |
| `swallow` | Swallow 8B | 4.9GB | 日本語特化、東工大開発 |
| `cydonia` | Cydonia 22B | 13.0GB | 創造的ロールプレイ向け |

### AI姉妹対話モード

```bash
# やなとあゆが自動で対話
/duo JetRacerのセンサー配置を改善したい
```

## プロジェクト構成

```
duo-talk-simple/
├── chat.py                  # メインCLI
├── config.yaml              # 設定ファイル
├── requirements.txt         # 依存関係
├── core/
│   ├── ollama_client.py     # Ollamaクライアント
│   ├── rag_engine.py        # RAG検索エンジン
│   ├── character.py         # キャラクター管理
│   ├── duo_dialogue.py      # AI同士対話管理
│   ├── prompt_builder.py    # プロンプト構築
│   └── conversation_logger.py # 会話ログ
├── personas/
│   ├── yana.yaml            # やな（姉）設定
│   └── ayu.yaml             # あゆ（妹）設定
├── patterns/
│   └── few_shot_patterns.yaml # Few-shotパターン
├── director/
│   └── director_rules.yaml  # Director介入ルール
├── knowledge/
│   ├── jetracer_tech.txt    # JetRacer技術情報
│   ├── jetracer_tech_with_perspectives.txt  # 視点付き技術情報
│   └── sisters_shared.txt   # 姉妹共有知識
├── logs/
│   ├── duo-talk.log         # システムログ
│   └── conversations/       # 会話ログ
├── tests/
│   ├── test_ollama_client.py
│   ├── test_rag_engine.py
│   ├── test_character.py
│   ├── test_prompt_builder.py
│   ├── test_duo_dialogue.py
│   ├── test_conversation_logger.py
│   ├── test_integration.py
│   ├── test_performance.py
│   └── test_e2e_cli.py      # CLI E2Eテスト
└── docs/
    ├── 00_プロジェクト概要.md
    ├── 01_アーキテクチャ設計.md
    ├── 02_コンポーネント詳細.md
    ├── 03_設定ファイル仕様.md
    ├── ...
    └── 10_改良仕様書.md
```

## テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=core --cov-report=html

# 高速テストのみ（LLM不要）
pytest tests/ -v -m "not slow"

# E2Eテストのみ
pytest tests/test_e2e_cli.py -v
```

### テスト結果（2026-01-19）

| カテゴリ | テスト数 | 状態 |
|----------|----------|------|
| OllamaClient | 13 | PASS |
| RAGEngine | 14 | PASS |
| Character | 11 | PASS |
| PromptBuilder | 4 | PASS |
| DuoDialogue | 35 | PASS |
| ConversationLogger | 12 | PASS |
| Integration | 5 | PASS |
| Performance | 5 | PASS |
| E2E CLI | 12 | PASS |
| **合計** | **114** | **ALL PASS** |

カバレッジ: **94%**

## 設定

### config.yaml 主要設定

| セクション | 説明 |
|------------|------|
| `ollama` | LLMモデル、タイムアウト設定 |
| `model_presets` | モデルプリセット（/modelで切り替え） |
| `rag` | ChromaDB、検索設定 |
| `knowledge` | 知識ベースファイル |
| `characters` | キャラクター別設定 |
| `duo_dialogue` | AI同士対話設定 |
| `conversation_log` | 会話ログ設定 |
| `logging` | システムログ設定 |

詳細は [docs/03_設定ファイル仕様.md](docs/03_設定ファイル仕様.md) を参照。

## TDD開発フロー

このプロジェクトはTDD（テスト駆動開発）で実装されました。

```
Phase 0: 環境構築
    ↓
Phase 1: OllamaClient (RED → GREEN)
    ↓
Phase 2: RAGEngine (RED → GREEN)
    ↓
Phase 3: Character (RED → GREEN)
    ↓
Phase 4: 統合テスト + chat.py
    ↓
Phase 5: 品質改善 + AI同士対話
```

## 関連ドキュメント

- [CONTRIB.md](docs/CONTRIB.md) - 開発ガイド
- [RUNBOOK.md](docs/RUNBOOK.md) - 運用ガイド
- [10_改良仕様書.md](docs/10_改良仕様書.md) - 改善計画

## ライセンス

MIT
