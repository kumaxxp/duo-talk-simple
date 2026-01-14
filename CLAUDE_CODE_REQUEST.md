# Claude Code への実装依頼メッセージ

以下をClaude Codeに送信してください：

---

## タスク: duo-talk-simple TDD実装（Phase 0 → Phase 5）

**プロジェクト**: duo-talk-simple  
**作業ディレクトリ**: `C:\work\duo-talk-simple`  
**開発方針**: テスト駆動開発（TDD） - Red → Green → Refactor

### 📚 必読ドキュメント

**実装指示書**: `IMPLEMENTATION_GUIDE.md`（最優先で確認）

**設計書**:
- `docs/01_アーキテクチャ設計.md`
- `docs/02_コンポーネント詳細.md`
- `docs/05_実装計画.md`（TDD方式）
- `docs/06_テスト戦略.md`（TDD戦略）
- `docs/07_実装サンプル.md`（コード例）
- `docs/08_設計レビュー報告書.md`（レビュー結果）

**設定ファイル**:
- `config.yaml`（システム設定）
- `personas/yana.yaml`（やなのペルソナ）
- `personas/ayu.yaml`（あゆのペルソナ）

### 🎯 実装方針

1. **テストファースト厳守**: 必ず実装前にテストを書く
2. **最小実装**: テストを通す最小限のコードのみ
3. **段階的実装**: Phase 0 → Phase 5まで順番に
4. **各Phase完了基準を満たしてから次へ進む**

### 📋 Phase 0: 環境準備（最初のタスク）

**参照**: `IMPLEMENTATION_GUIDE.md` Phase 0セクション

#### タスク一覧

1. **ディレクトリ作成**
   ```powershell
   New-Item -ItemType Directory -Path core, tests, data, logs -Force
   New-Item -ItemType File -Path core\__init__.py, tests\__init__.py -Force
   ```

2. **requirements.txt作成**
   - 必要なライブラリを記載
   - 参照: `IMPLEMENTATION_GUIDE.md` タスク 0.2

3. **pytest.ini作成**
   - pytest設定
   - 参照: `IMPLEMENTATION_GUIDE.md` タスク 0.3

4. **依存ライブラリインストール**
   ```bash
   pip install -r requirements.txt
   ```

5. **Ollama動作確認**
   ```bash
   ollama --version
   ollama run gemma3:12b
   # プロンプト: "こんにちは" → 応答確認
   ```

6. **pytest動作確認**
   ```bash
   pytest --version
   pytest tests/ -v
   # "no tests ran" と表示されればOK
   ```

#### Phase 0 完了基準

- [ ] ディレクトリ構成完成
- [ ] requirements.txt作成・インストール完了
- [ ] pytest.ini作成
- [ ] Ollama動作確認
- [ ] pytest動作確認

**Phase 0完了後、報告してください。**

---

### 📋 Phase 1: OllamaClient（TDD）

**Phase 0完了後に開始**

**参照**: 
- `IMPLEMENTATION_GUIDE.md` Phase 1セクション
- `docs/07_実装サンプル.md` 1.1（実装例）
- `docs/07_実装サンプル.md` 6.1（テスト例）

#### TDDサイクル

1. **RED**: `tests/test_ollama_client.py` 作成
   - `test_init()` から開始
   - pytest実行 → 失敗確認

2. **GREEN**: `core/ollama_client.py` 実装
   - 最小限の実装
   - pytest実行 → 成功確認

3. **REFACTOR**: コード改善
   - pytest実行 → 成功維持確認

4. **繰り返し**: 残りのテストケース（7件）

#### Phase 1 完了基準

- [ ] 全テスト成功（7件）
- [ ] カバレッジ > 80%
- [ ] Ollama接続動作確認

**Phase 1完了後、報告してください。**

---

### 📋 Phase 2: RAGEngine（TDD）

**Phase 1完了後に開始**

**参照**: 
- `IMPLEMENTATION_GUIDE.md` Phase 2セクション
- `docs/07_実装サンプル.md` 2.1（実装例）
- `docs/07_実装サンプル.md` 6.2（テスト例）

#### 重要

- 知識ファイル投入テストを含む
- `knowledge/jetracer_tech.txt` と `knowledge/sisters_shared.txt` は既に存在

#### Phase 2 完了基準

- [ ] 全テスト成功（8件）
- [ ] カバレッジ > 80%
- [ ] ChromaDB永続化確認
- [ ] 知識ファイル投入成功

**Phase 2完了後、報告してください。**

---

### 📋 Phase 3: Character（TDD）

**Phase 2完了後に開始**

**参照**: 
- `IMPLEMENTATION_GUIDE.md` Phase 3セクション
- `docs/07_実装サンプル.md` 3.1（実装例）
- `docs/07_実装サンプル.md` 6.3（テスト例）

#### 重要

- ペルソナYAML読み込み処理
- キャラクター性の確認（手動テスト）
  - やなは丁寧語を使わない
  - あゆは姉を「姉様」と呼ぶ

#### Phase 3 完了基準

- [ ] 全テスト成功（7件）
- [ ] やな・あゆの口調確認
- [ ] RAG統合動作確認
- [ ] 手動確認: キャラクター性

**Phase 3完了後、報告してください。**

---

### 📋 Phase 4: 統合（TDD）

**Phase 3完了後に開始**

**参照**: 
- `IMPLEMENTATION_GUIDE.md` Phase 4セクション
- `docs/07_実装サンプル.md` 5.1（chat.py実装例）
- `docs/07_実装サンプル.md` 6.4（統合テスト例）

#### 実装内容

1. `tests/test_integration.py` 作成
2. `chat.py` 実装（メインアプリケーション）
3. 動作確認

#### Phase 4 完了基準

- [ ] 統合テスト全成功（5件）
- [ ] chat.py起動成功
- [ ] やな・あゆ切り替え動作
- [ ] コマンド動作（/switch, /clear, /exit）

**Phase 4完了後、報告してください。**

---

### 📋 Phase 5: 品質向上

**Phase 4完了後に開始**

**参照**: 
- `IMPLEMENTATION_GUIDE.md` Phase 5セクション
- `docs/07_実装サンプル.md` 6.5（パフォーマンステスト例）

#### 実装内容

1. カバレッジ確認
2. `tests/test_performance.py` 作成
3. `README.md` 作成

#### Phase 5 完了基準

- [ ] カバレッジ > 80%
- [ ] パフォーマンステスト合格
- [ ] README.md作成

**Phase 5完了後、最終報告してください。**

---

## 🎯 全体完成基準

### 必須条件
- [ ] Phase 0-5 全て完了
- [ ] 全テスト成功（100%）
- [ ] カバレッジ > 80%
- [ ] chat.py動作確認

### 報告形式

各Phase完了時:
```
## Phase X 完了報告

### 実施内容
- 作成ファイル: X件
- テスト成功: X件
- カバレッジ: XX%

### 確認事項
- [x] 設計書との整合性
- [x] テスト成功
- [x] 動作確認

### 次のアクション
Phase X+1に進みます
```

---

## ⚠️ 重要な注意事項

1. **必ず `IMPLEMENTATION_GUIDE.md` を最初に確認**
2. **テストファースト厳守**（実装前に必ずテストを書く）
3. **各Phaseの完了基準を満たしてから次へ進む**
4. **設計書（docs/）を常に参照**
5. **実装例（docs/07_実装サンプル.md）を活用**

---

## 🚀 開始コマンド

```bash
cd C:\work\duo-talk-simple
python -m pytest --version
```

**Phase 0から開始してください。頑張ってください！**
