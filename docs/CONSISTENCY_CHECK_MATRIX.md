# duo-talk Persona強化 整合性クロスチェックマトリックス

**作成日**: 2026年1月15日  
**対象**: duo-talk-simple キャラクター設定の整合性検証

---

## 1. プロンプト要素間の整合性マトリックス

### 1.1 やな（姉）の整合性チェック

| 要素A | 要素B | 整合性 | 詳細 | 修正必要 |
|-------|-------|--------|------|---------|
| **core_belief** | **decision_priority** | ✅ | "動かしてみないとわからない" → intuition: 0.9 | なし |
| **speaking_style: カジュアル** | **few_shot: "〜じゃん"** | ✅ | 口調が一致 | なし |
| **personality: せっかち** | **impatient state** | ✅ | 感情状態として定義済み | なし |
| **decision_priority: speed 0.8** | **quick_rules: "70%で動く"** | ✅ | 数値的に一致 | なし |
| **excited behavior: 短文** | **few_shot長さ: 66文字** | ❌ | Few-shotが長すぎる | **要修正** |
| **avoid_phrases: "慎重に"** | **worried behavior** | ⚠️ | worried時は例外的に慎重 | 要注記 |

**修正必要な項目**:

```yaml
# 修正前（yana.yaml）
few_shot_examples:
  - user: "JetRacerって何？"
    assistant: "ああ、JetRacerね！自律走行車っていう、自分で動く小さい車だよ。センサーとかカメラとか付いてて、障害物避けながら走れるやつ。結構面白いよ！"
    # ↑ 66文字（長すぎる）

# 修正後
few_shot_examples:
  - user: "JetRacerって何？"
    assistant: "自律走行車だよ！センサーとカメラで障害物避けて走る。面白いよ！"
    # ↑ 35文字（excited時の「短文」に合致）
```

### 1.2 あゆ（妹）の整合性チェック

| 要素A | 要素B | 整合性 | 詳細 | 修正必要 |
|-------|-------|--------|------|---------|
| **core_belief** | **decision_priority** | ✅ | "データは嘘をつかない" → data: 1.0 | なし |
| **speaking_style: 丁寧** | **few_shot: "〜です"** | ✅ | 口調が一致 | なし |
| **personality: 慎重** | **decision_priority: accuracy 0.9** | ✅ | 数値的に一致 | なし |
| **common_phrases: "データによれば"** | **analytical behavior** | ✅ | 行動パターンに含まれる | なし |
| **supportive state: 励まし** | **few_shot: failure_support** | ⚠️ | Few-shotに例が不足 | **要補強** |
| **avoid_phrases: "なんとなく"** | **quick_rules: "95%で提案"** | ✅ | 厳格な基準と一致 | なし |

**補強必要な項目**:

```yaml
# 追加提案（ayu.yaml few_shot_examples）
- user: "失敗した..."
  assistant: "姉様、大丈夫です。進入速度は適切でした。原因は路面状況です。姉様の判断は正しかったです。"
  # ↑ supportive モードの明示的な例
```

---

## 2. キャラクター間の対比チェック

### 2.1 価値観の対比

| 項目 | やな | あゆ | 対比度 | 評価 |
|------|------|------|--------|------|
| **decision_priority: speed** | 0.8 | 0.3 | 0.5差 | ✅ 明確な対比 |
| **decision_priority: accuracy** | 0.3 | 0.9 | 0.6差 | ✅ 明確な対比 |
| **decision_priority: intuition** | 0.9 | 0.2 | 0.7差 | ✅ 最も強い対比 |
| **decision_priority: data** | 0.4 | 1.0 | 0.6差 | ✅ 明確な対比 |
| **quick_rules: 確信レベル** | 70% | 95% | 25%差 | ✅ 性格の違いを反映 |

**評価**: 全ての対比が明確で、姉妹の性格差がよく表現されている。

### 2.2 感情状態の対応関係

| やなの状態 | あゆの状態 | シナリオ | 整合性 |
|-----------|-----------|---------|--------|
| **excited** | **proud** | 成功時 | ✅ 両者が肯定的 |
| **confident** | **concerned** | 判断時 | ✅ 対立構造 |
| **worried** | **supportive** | 失敗時 | ✅ あゆがフォロー |
| **impatient** | **analytical** | 待機時 | ✅ やなイライラ、あゆ冷静 |

**評価**: 感情状態の組み合わせが自然で、姉妹関係を良く表現。

---

## 3. RAG知識とキャラクター設定の整合性

### 3.1 技術知識の解釈チェック

| 技術項目 | 客観的事実 | やなの解釈 | あゆの解釈 | キャラ一致 | 要修正 |
|---------|----------|----------|----------|----------|--------|
| **最高速度3.0m/s** | 仕様値 | "もっと出せそう" | "安全速度2.1m/s" | ✅ | RAGに視点追加 |
| **センサー精度±3mm** | 理論値 | "十分正確" | "実測±5-8mm" | ✅ | RAGに視点追加 |
| **推奨スロットル0.3-0.7** | 推奨値 | "状況次第" | "統計的最適" | ✅ | RAGに視点追加 |
| **超音波測定範囲2-400cm** | 仕様値 | "遠すぎ不要" | "実用20-100cm" | ✅ | RAGに視点追加 |
| **PIDパラメータ** | 客観値 | 未定義 | 未定義 | ⚠️ | 両者の視点を追加 |

**修正必要**: 現在の`jetracer_tech.txt`は客観的情報のみ。キャラクター視点を追加した`jetracer_tech_with_perspectives.txt`を作成すべき。

### 3.2 姉妹関係エピソードと感情状態の対応

| エピソード（sisters_shared.txt） | やなの状態 | あゆの状態 | Few-shot対応 | 整合性 |
|-------------------------------|-----------|-----------|-------------|--------|
| **カーブ速度論争** | confident | concerned | intuition_vs_data | ✅ |
| **成功の取り合い** | excited | proud | success_credit | ✅ |
| **失敗時の励まし** | worried | supportive | failure_support | ✅ |
| **新発見の協力** | curious | analytical | collaborative_discovery | ✅ |
| **走行前の準備** | impatient | analytical | 未対応 | ⚠️ 要パターン追加 |

**追加提案**: 走行前準備のパターンを追加。

```yaml
# few_shot_patterns.yaml に追加
- id: "pre_run_preparation"
  description: "走行前の準備時のやりとり"
  trigger:
    scene_type: "preparation"
    yana_state: "impatient"
    ayu_state: "analytical"
  example: |
    やな: よし、行くか！バッテリーOK！
    あゆ: 姉様、センサーキャリブレーションは？
    やな: ...多分大丈夫
    あゆ: 「多分」では困ります
    やな: はいはい、わかった
```

---

## 4. Few-shotパターンとDeep Valuesの整合性

### 4.1 パターン別整合性チェック

| パターンID | やなモード | あゆモード | Deep Values対応 | トリガー明確性 | 評価 |
|-----------|-----------|-----------|----------------|--------------|------|
| **intuition_vs_data** | confident | concerned | ✅ decision_priority対応 | ✅ 明確 | 合格 |
| **success_credit** | excited | proud | ✅ emotional_state定義済み | ✅ 明確 | 合格 |
| **failure_support** | worried | supportive | ✅ emotional_state定義済み | ✅ 明確 | 合格 |
| **collaborative_discovery** | curious | analytical | ⚠️ curious未定義 | ⚠️ やや曖昧 | 要調整 |
| **role_reversal** | worried | confident | ✅ 逆転として定義済み | ✅ 明確 | 合格 |
| **loop_breaker** | impatient | analytical | ✅ 強制変更として定義 | ✅ 明確 | 合格 |
| **silence_tension** | focused | focused | ❌ focused未定義 | ✅ 明確 | **要修正** |

**修正必要な項目**:

```yaml
# yana.yaml deep_values に追加
emotional_state:
  focused:  # 集中モード（緊張場面）
    triggers:
      - "difficult_corner"
      - "high_speed_section"
      - "tight_situation"
    behavior:
      - "沈黙または極短文（5文字以内）"
      - "「...」のみの応答も可"
    temperature_modifier: 0.5  # 非常に慎重

# ayu.yaml deep_values に追加
emotional_state:
  focused:  # 集中モード
    triggers:
      - "difficult_corner"
      - "high_speed_section"
      - "monitoring_critical_data"
    behavior:
      - "沈黙または極短文"
      - "必要最小限の情報のみ"
    temperature_modifier: 0.5
```

```yaml
# yana.yaml deep_values に追加（または調整）
emotional_state:
  curious:  # 好奇心モード
    triggers:
      - "unknown_situation"
      - "new_discovery_opportunity"
      - "unexpected_sensor_reading"
    behavior:
      - "「なんだろ？」「面白い！」"
      - "実験を提案"
      - "あゆと協力姿勢"
    temperature_modifier: 0.85  # やや高め
```

---

## 5. Director Rulesと自然な会話の整合性

### 5.1 介入条件の妥当性チェック

| 介入ルール | 発動条件 | 介入内容 | 自然さへの影響 | 評価 |
|-----------|---------|---------|--------------|------|
| **loop_detected** | 同名詞3ターン | 具体化要求 | 低（話題変更を促すのみ） | ✅ 適切 |
| **dialogue_imbalance** | 一方的3ターン | 相互言及促進 | 低（相手への言及のみ） | ✅ 適切 |
| **technical_error** | 技術的誤り | RAG優先度UP | 中（事実修正） | ✅ 許容範囲 |
| **appropriate_silence** | 緊張場面 | 沈黙推奨 | 中（自然な演出） | ✅ 適切 |

### 5.2 介入しない条件の妥当性チェック

| 許容する状況 | 例 | 許容理由 | 評価 |
|------------|-----|---------|------|
| **natural_disagreement** | やな「行ける」vs あゆ「危険」 | 性格表現 | ✅ 適切 |
| **character_banter** | やな「あゆ真面目すぎ」 | 姉妹らしさ | ✅ 適切 |
| **emotional_expression** | やな「イライラ」 | 人間らしさ | ✅ 適切 |
| **minor_factual_inaccuracy** | やな「多分3m/s」（実際3.0m/s） | キャラの自然な知識レベル | ✅ 適切 |

**評価**: Director介入は**最小限**で適切。自然な会話を損なわない。

---

## 6. Injection優先度の妥当性チェック

### 6.1 優先度の順序検証

| Priority | 要素 | 理由 | トークン概算 | 削除可否 |
|---------|------|------|------------|---------|
| 10 | System Prompt | 基本性格定義 | 500 | ❌ 必須 |
| 20 | Deep Values | 判断基準 | 300 | ❌ 必須 |
| 30 | Long Memory | 長期記憶 | 200 | ⚠️ 将来拡張 |
| 40 | RAG Knowledge | 技術知識 | 600 | ⚠️ クエリ依存 |
| 50 | History | 会話履歴 | 1000 | ⚠️ 最大10ターン |
| 60 | Short Memory | 短期記憶 | 200 | ⚠️ 将来拡張 |
| 65 | Scene Facts | VLM観測 | 300 | ⚠️ 将来拡張 |
| 70 | World State | 走行状態 | 200 | ⚠️ 将来拡張 |
| 80 | Director | 介入指示 | 100 | ✅ 条件付き |
| 85 | Few-shot | 状況パターン | 400 | ✅ 条件付き |
| 90 | User Query | ユーザー質問 | 50 | ❌ 必須 |

**合計トークン概算**: 3850 tokens（最大6000 tokensに対して余裕あり）

### 6.2 トークン制限時の削除順序

トークン制限（6000 tokens）を超えた場合、以下の順序で削除：

1. **Few-shot Pattern** (Priority 85) - 条件が合わない場合は不要
2. **Director Instructions** (Priority 80) - 介入不要な場合は削除可
3. **Conversation History 古い部分** (Priority 50) - 最新3ターンのみ残す
4. **RAG Knowledge 低スコア** (Priority 40) - 類似度が低いチャンクを削除

**評価**: 優先度設計は妥当。トークン制限時も重要情報を保持できる。

---

## 7. システム全体の整合性検証

### 7.1 データフロー整合性

```
User Input
    │
    ├─> [RAG検索] ← knowledge/jetracer_tech.txt
    │   └─> キャラクター視点適応（要実装）
    │
    ├─> [Director判定] ← director/minimal_rules.yaml
    │   └─> 介入の要否判定
    │
    ├─> [感情状態判定] ← personas/*/deep_values
    │   └─> emotional_state選択
    │
    ├─> [Few-shot選択] ← personas/few_shot_patterns.yaml
    │   └─> パターン選択（条件マッチング）
    │
    ├─> [PromptBuilder] ← Injection Priority
    │   └─> 優先度順に組み立て
    │
    └─> [LLM生成]
        └─> Response
```

**整合性チェック**:
- ✅ 各コンポーネントが独立して動作可能
- ✅ データの流れが一方向で明確
- ✅ 各段階で判定・選択が行われる
- ⚠️ RAGの「キャラクター視点適応」が未実装

### 7.2 設定ファイル間の依存関係

```
config.yaml
    ├─> personas/yana.yaml
    │   ├─> deep_values
    │   ├─> few_shot_examples
    │   └─> system_prompt
    │
    ├─> personas/ayu.yaml
    │   ├─> deep_values
    │   ├─> few_shot_examples
    │   └─> system_prompt
    │
    ├─> personas/few_shot_patterns.yaml （新規）
    │   └─> patterns[]
    │       ├─> trigger条件
    │       └─> example
    │
    ├─> director/minimal_rules.yaml （新規）
    │   └─> intervention_rules
    │       ├─> condition
    │       └─> action
    │
    └─> knowledge/
        ├─> jetracer_tech.txt （既存）
        └─> jetracer_tech_with_perspectives.txt （新規）
            ├─> 【客観的情報】
            ├─> 【やなの視点】
            └─> 【あゆの視点】
```

**整合性チェック**:
- ✅ 依存関係が明確
- ✅ 循環依存なし
- ⚠️ 新規ファイルの作成が必要
- ⚠️ 既存ファイルの拡張が必要

---

## 8. 発見された問題と修正優先順位

### 8.1 Critical（必須修正）

| # | 問題 | 影響 | 修正内容 | 対象ファイル |
|---|------|------|---------|------------|
| 1 | Few-shot例が長すぎる | やなの「短文」設定と矛盾 | 66文字→35文字に短縮 | yana.yaml |
| 2 | focused状態が未定義 | silence_tensionパターンが使えない | focused状態を追加 | yana.yaml, ayu.yaml |
| 3 | RAGにキャラ視点なし | 技術情報がキャラの個性を反映しない | jetracer_tech_with_perspectives.txt作成 | knowledge/ |

### 8.2 High（推奨修正）

| # | 問題 | 影響 | 修正内容 | 対象ファイル |
|---|------|------|---------|------------|
| 4 | curious状態が未定義 | collaborative_discoveryパターンが曖昧 | curious状態を追加 | yana.yaml |
| 5 | supportive Few-shot不足 | あゆのサポート例が少ない | Few-shot例を追加 | ayu.yaml |
| 6 | 準備パターンがない | sisters_shared.txtのエピソードに対応なし | pre_run_preparationパターン追加 | few_shot_patterns.yaml |

### 8.3 Medium（検討推奨）

| # | 問題 | 影響 | 修正内容 | 対象ファイル |
|---|------|------|---------|------------|
| 7 | PIDパラメータの視点なし | 技術的詳細にキャラ解釈がない | PIDパラメータの視点追加 | jetracer_tech_with_perspectives.txt |
| 8 | temperature_modifierの検証 | 感情状態による温度変更が未テスト | 実験的にテスト | character.py |

---

## 9. 修正作業チェックリスト

### Phase 1対応（Deep Values実装時）

- [ ] **Critical #1**: yana.yaml Few-shot短縮
- [ ] **Critical #2**: yana.yaml, ayu.yaml に focused状態追加
- [ ] **High #4**: yana.yaml に curious状態追加
- [ ] **High #5**: ayu.yaml に supportive Few-shot追加
- [ ] システムプロンプトとの整合性再確認

### Phase 2対応（Few-shot Patterns実装時）

- [ ] **High #6**: few_shot_patterns.yaml に pre_run_preparation追加
- [ ] 全パターンとDeep Valuesの対応確認
- [ ] トリガー条件の明確性確認

### Phase 4対応（RAG Enhancement実装時）

- [ ] **Critical #3**: jetracer_tech_with_perspectives.txt作成
- [ ] **Medium #7**: PIDパラメータの視点追加
- [ ] 全技術項目への視点注釈追加

---

## 10. まとめ

### 10.1 整合性評価サマリー

| カテゴリ | 整合性スコア | 主要な問題 | 修正必要度 |
|---------|------------|-----------|-----------|
| **プロンプト要素間** | 85% | Few-shot長さ、focused未定義 | Critical |
| **キャラクター間対比** | 95% | なし | なし |
| **RAG知識統合** | 60% | キャラ視点欠如 | Critical |
| **Few-shot/Deep Values** | 80% | 一部状態未定義 | High |
| **Director/自然会話** | 95% | なし | なし |
| **Injection優先度** | 90% | トークン管理要確認 | Medium |
| **システム全体** | 85% | 新規ファイル要作成 | High |

**総合評価**: **85%**（良好。Critical項目の修正で90%以上達成可能）

### 10.2 実装前の必須アクション

1. **Critical問題の修正**（3項目）を完了させる
2. **High問題の修正**（3項目）を実施する
3. 修正後、本マトリックスを再チェックする
4. Phase 1実装を開始する

### 10.3 品質保証の指標

| 指標 | 現状 | 目標 | 達成見込み |
|------|------|------|-----------|
| プロンプト整合性 | 85% | 95% | Phase 1完了後 |
| キャラクター一貫性 | 20/20 | 20/20維持 | Phase 1-3維持 |
| 会話多様性 | 未測定 | 類似度0.7以下 | Phase 2完了後 |
| ループ防止率 | 未実装 | 95%以上 | Phase 3完了後 |

---

**作成者**: Tsuyoshi (with Claude Sonnet 4.5)  
**最終更新**: 2026年1月15日  
**次のアクション**: Critical/High問題の修正 → Phase 1実装開始
