# duo-talk-simple Project Knowledge

## プロジェクト概要

姉妹AI（やな/あゆ）によるJetRacer自律走行の実況・解説対話システム。
Ollama + ChromaDB (RAG) で構築されたCLIアプリケーション。

| 項目 | 値 |
|------|-----|
| 言語 | Python 3.12+ |
| LLM | Ollama (gemma3:12b) |
| 埋め込み | mxbai-embed-large |
| ベクトルDB | ChromaDB |
| テスト | pytest (94% coverage, 108 tests) |

---

## アーキテクチャ

```
User Input
    │
    ▼
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ chat.py  │ ──▶ │ Character │ ──▶ │ RAGEngine    │
└──────────┘     │           │     │ (search)     │
                 │           │     └──────────────┘
                 │           │            │
                 │           │     ┌──────────────┐
                 │           │ ──▶ │PromptBuilder │
                 │           │     └──────────────┘
                 │           │            │
                 │           │     ┌──────────────┐
                 │           │ ──▶ │ OllamaClient │
                 │           │     │ (generate)   │
                 └───────────┘     └──────────────┘
                       │
                       ▼
                 ┌───────────┐
                 │ Response  │
                 └───────────┘
```

---

## 主要コンポーネント

| コンポーネント | ファイル | 責務 |
|---------------|---------|------|
| OllamaClient | `core/ollama_client.py` | LLMバックエンド通信、テキスト生成、埋め込み生成 |
| RAGEngine | `core/rag_engine.py` | ChromaDBによる知識検索、ベクトル類似度検索、**視点抽出** |
| Character | `core/character.py` | キャラクター応答生成、履歴管理、状態推定 |
| PromptBuilder | `core/prompt_builder.py` | システムプロンプト構築、Persona読込、Few-shot選択 |
| DuoDialogueManager | `core/duo_dialogue.py` | AI同士対話の制御、ターン管理、収束検知 |
| ConversationLogger | `core/conversation_logger.py` | 会話ログの永続化 |

### 視点抽出機能（Phase 2A）

RAGエンジンが知識を返す際、キャラクターの視点に応じて抽出:

```
【客観】
- センサーは周囲の障害物を検出する

【やなの視点】
- まず動かしてみて感覚を掴む ← やなが検索時に取得

【あゆの視点】
- 統計分析が重要 ← あゆが検索時に取得
```

---

## キャラクター設計原則（重要）

### やな（姉 / Edge AI的存在）

```yaml
core_belief: "動かしてみなきゃわからない"
personality: [直感的, 楽観的, せっかち, 好奇心旺盛]
style: カジュアル、短文、速いテンポ
role: 発見者、試行者、突破口を開く
```

**典型的な発言パターン:**
- 「平気平気！」
- 「まあまあ、やってみようよ」
- 「あゆがなんとかしてくれるでしょ」

### あゆ（妹 / Cloud AI的存在）

```yaml
core_belief: "姉の無計画さをデータで殴るのが仕事"
personality: [論理的, 冷静, 慎重, 少し皮肉屋]
style: 丁寧語、短文、中テンポ
role: ツッコミ役、ブレーキ役、検証者
```

**典型的な発言パターン:**
- 「ちょっと待ってください」
- 「根拠があるのでしょうか？」
- 「前回もそれで失敗しましたよね」
- 「...まあ、やな姉様がそう言うなら」

### 絶対禁止事項

```
- AIアシスタント的発言（「何かお手伝いできることはありますか？」）
- 技術用語の羅列・説明口調
- 即座の同意（「なるほど」「確かに」「いいですね」）
- 従順すぎる態度
- 長すぎる説明や前置き
```

---

## CLIコマンド一覧

| コマンド | 説明 |
|----------|------|
| `/switch` | キャラクター切り替え（やな⇔あゆ） |
| `/duo <お題>` | AI姉妹対話モード開始 |
| `/clear` | 会話履歴クリア |
| `/status` | 現在の状態表示 |
| `/debug` | RAGデバッグ表示切替 |
| `/help` | コマンド一覧表示 |
| `/exit` | 終了（ログ保存） |

---

## 設定ファイル構造

```
duo-talk-simple/
├── config.yaml              # メイン設定（LLM/RAG/ログ）
├── personas/
│   ├── yana.yaml            # やな（姉）定義
│   └── ayu.yaml             # あゆ（妹）定義
├── patterns/
│   └── few_shot_patterns.yaml  # Few-shotパターン
└── director/
    └── director_rules.yaml  # Director介入ルール
```

### config.yaml 主要セクション

| セクション | 説明 |
|------------|------|
| `ollama` | LLMモデル、URL、タイムアウト |
| `rag` | ChromaDB設定、検索パラメータ |
| `knowledge` | 知識ベースファイル定義 |
| `characters` | キャラクター別generation設定 |
| `duo_dialogue` | AI同士対話設定（max_turns等） |
| `logging` | ログレベル、ファイル出力 |

---

## 開発規約

### TDD必須（テストファースト）

```
1. RED    - 失敗するテストを書く
2. GREEN  - テストが通る最小限のコードを書く
3. REFACTOR - コード品質を改善する
```

### カバレッジ要件

- **最低**: 80%
- **現在**: 93%
- **目標**: 90%以上を維持

### コード品質

```bash
# フォーマット
black chat.py core/ tests/

# Lint
flake8 chat.py core/ --max-line-length=100

# Dead code検出
vulture chat.py core/ --min-confidence 80
```

### テストパス必須

```bash
# 全テスト実行（コミット前に必ず実行）
pytest tests/ -v
```

---

## テスト構造

```
tests/
├── test_ollama_client.py      # OllamaClient単体テスト (7)
├── test_rag_engine.py         # RAGEngine単体テスト (14)  ★Phase 2A拡充
├── test_character.py          # Character単体テスト (11)  ★Phase 2A拡充
├── test_prompt_builder.py     # PromptBuilder単体テスト (4)
├── test_duo_dialogue.py       # DuoDialogue単体テスト (34)  ★Phase 1拡充
├── test_conversation_logger.py # Logger単体テスト (16)
├── test_integration.py        # 統合テスト (5)
├── test_performance.py        # パフォーマンステスト (5)
└── test_e2e_cli.py            # CLI E2Eテスト (12) [pexpect]
```

**合計**: 108テスト

---

## よく使うコマンド

```bash
# アプリ起動
python chat.py

# 全テスト実行
pytest tests/ -v

# カバレッジ計測
pytest tests/ --cov=core --cov-report=html

# 高速テストのみ（LLM不要）
pytest tests/ -v -m "not slow"

# E2Eテストのみ
pytest tests/test_e2e_cli.py -v

# Lint
flake8 chat.py core/ --max-line-length=100

# フォーマット
black chat.py core/ tests/

# Ollama状態確認
curl http://localhost:11434/api/tags
```

---

## ファイル変更時の注意

### personas/*.yaml を変更した場合

- Few-shotパターン（`patterns/few_shot_patterns.yaml`）との整合性を確認
- 対応するテスト（`test_prompt_builder.py`）を実行

### core/*.py を変更した場合

- 対応するユニットテストを実行
- 統合テスト（`test_integration.py`）を実行
- カバレッジが80%以上であることを確認

### config.yaml を変更した場合

- アプリ起動テスト（`python chat.py` でエラーが出ないこと）
- E2Eテスト（`test_e2e_cli.py`）を実行

---

## 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| [docs/CONTRIB.md](docs/CONTRIB.md) | 開発ガイド |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | 運用ガイド |
| [docs/codemaps/architecture.md](docs/codemaps/architecture.md) | アーキテクチャ図 |
| [docs/codemaps/core.md](docs/codemaps/core.md) | コアモジュールAPI |
| [docs/codemaps/data.md](docs/codemaps/data.md) | データモデル定義 |
| [docs/10_改良仕様書.md](docs/10_改良仕様書.md) | 改善計画 |
