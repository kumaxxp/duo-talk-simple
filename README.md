# duo-talk-simple

TDD方式で実装した、姉妹AIによるJetRacer対話システム

## 概要

「やな」と「あゆ」という二人の姉妹AIが、JetRacer（自律走行車）についてお話しします。

- **やな（姉）**: 直感的・行動派、カジュアルな口調
- **あゆ（妹）**: 分析的・慎重派、丁寧な口調

## 必要環境

- Python 3.12+
- Ollama（ローカルLLM）
- 推奨VRAM: 12GB以上

### Ollamaモデル

```bash
ollama pull gemma3:12b        # LLM
ollama pull mxbai-embed-large # 埋め込み
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

### コマンド

| コマンド | 説明 |
|----------|------|
| `/switch` | キャラクター切り替え |
| `/clear` | 会話履歴クリア |
| `/status` | 状態表示 |
| `/help` | ヘルプ表示 |
| `/exit` | 終了 |

## プロジェクト構成

```
duo-talk-simple/
├── chat.py              # メインCLI
├── config.yaml          # 設定ファイル
├── core/
│   ├── ollama_client.py # Ollamaクライアント
│   ├── rag_engine.py    # RAG検索エンジン
│   └── character.py     # キャラクター管理
├── personas/
│   ├── yana.yaml        # やな（姉）設定
│   └── ayu.yaml         # あゆ（妹）設定
├── knowledge/
│   ├── jetracer_tech.txt    # JetRacer技術情報
│   └── sisters_shared.txt   # 姉妹共有知識
└── tests/
    ├── test_ollama_client.py
    ├── test_rag_engine.py
    ├── test_character.py
    ├── test_integration.py
    └── test_performance.py
```

## テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=core --cov-report=html

# パフォーマンステストのみ
pytest tests/test_performance.py -v -s
```

### テスト結果

| カテゴリ | テスト数 | 状態 |
|----------|----------|------|
| OllamaClient | 7 | PASS |
| RAGEngine | 8 | PASS |
| Character | 7 | PASS |
| Integration | 5 | PASS |
| Performance | 5 | PASS |
| **合計** | **32** | **ALL PASS** |

カバレッジ: **92%**

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
Phase 5: 品質改善
```

## ライセンス

MIT
