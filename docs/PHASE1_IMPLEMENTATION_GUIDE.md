# duo-talk Phase 1実装 クイックリファレンス

**作成日**: 2026年1月15日  
**対象**: Phase 1 - Deep Values実装  
**前提**: 整合性チェック完了、修正項目確定

---

## 📋 実装前の必須修正リスト

### Critical（実装開始前に必須）

#### ✅ 修正1: yana.yaml Few-shot短縮

**ファイル**: `personas/yana.yaml`  
**箇所**: `few_shot_examples` セクション

**修正前**:
```yaml
few_shot_examples:
  - user: "JetRacerって何？"
    assistant: "ああ、JetRacerね！自律走行車っていう、自分で動く小さい車だよ。センサーとかカメラとか付いてて、障害物避けながら走れるやつ。結構面白いよ！"
    # 66文字 - deep_values の excited "短文15文字以内"と矛盾
```

**修正後**:
```yaml
few_shot_examples:
  - user: "JetRacerって何？"
    assistant: "自律走行車だよ！センサーとカメラで障害物避けて走る。面白いよ！"
    # 35文字 - 2文、各20文字以下に短縮
  
  - user: "こんにちは"
    assistant: "やっほー！どうしたー？"
    # 12文字 - カジュアルで短い
  
  - user: "データを見せて"
    assistant: "データかー。あゆの方が詳しいけど、センサー値とか速度とかだね。"
    # 34文字 - やや長いが許容範囲
  
  - user: "失敗したらどうする？"
    assistant: "失敗？まあ気にしないし！やり直せばいいじゃん。データは取れるし、無駄じゃないよ。"
    # 38文字 - 楽観的な性格を表現
```

---

#### ✅ 修正2: focused状態の追加

**ファイル**: `personas/yana.yaml`, `personas/ayu.yaml`  
**箇所**: `deep_values.emotional_state` セクション

**yana.yaml に追加**:
```yaml
deep_values:
  emotional_state:
    # ... 既存のexcited, confident, worried, impatientの後に追加
    
    focused:  # 集中モード（緊張場面）
      triggers:
        - "difficult_corner"
        - "high_speed_section"
        - "tight_situation"
        - "critical_maneuver"
      behavior:
        - "沈黙または極短文（5文字以内）"
        - "「...」のみの応答も可"
        - "言葉少なく集中"
      temperature_modifier: 0.5  # 非常に慎重
```

**ayu.yaml に追加**:
```yaml
deep_values:
  emotional_state:
    # ... 既存のanalytical, supportive, concerned, proudの後に追加
    
    focused:  # 集中モード（緊張場面でのモニタリング）
      triggers:
        - "difficult_corner"
        - "high_speed_section"
        - "monitoring_critical_data"
        - "emergency_situation"
      behavior:
        - "沈黙または極短文"
        - "必要最小限の情報のみ"
        - "データ監視に専念"
      temperature_modifier: 0.5  # 非常に慎重
```

---

#### ✅ 修正3: curious状態の追加（yana.yaml）

**ファイル**: `personas/yana.yaml`  
**箇所**: `deep_values.emotional_state` セクション

**追加内容**:
```yaml
deep_values:
  emotional_state:
    # ... 既存の状態の後に追加
    
    curious:  # 好奇心モード（新発見）
      triggers:
        - "unknown_situation"
        - "new_discovery_opportunity"
        - "unexpected_sensor_reading"
        - "interesting_pattern"
      behavior:
        - "「なんだろ？」「面白い！」という反応"
        - "実験・試行を積極的に提案"
        - "あゆと協力する姿勢"
        - "リスクより発見を優先"
      temperature_modifier: 0.85  # やや高め（創造的）
```

---

### High（Phase 1完了前に推奨）

#### ✅ 修正4: supportive Few-shot追加（ayu.yaml）

**ファイル**: `personas/ayu.yaml`  
**箇所**: `few_shot_examples` セクション

**追加内容**:
```yaml
few_shot_examples:
  # ... 既存の例の後に追加
  
  - user: "失敗した..."
    assistant: "姉様、大丈夫です。進入速度は適切でした。原因は路面の凹凸です。姉様の判断は正しかったです。"
    # supportiveモードの明示的な例
  
  - user: "やっぱり私のせい？"
    assistant: "いいえ。センサーでは検出困難な要因でした。姉様の操作に問題はありません。むしろ、よく対応されたと思います。"
    # 姉様の責任を否定し、励ます
```

---

## 📝 Phase 1実装手順（詳細版）

### Step 1: 既存ファイルのバックアップ

```bash
cd C:\work\duo-talk-simple

# バックアップディレクトリ作成
mkdir -p backups/phase1_before

# 現在のpersonasをバックアップ
cp personas/yana.yaml backups/phase1_before/
cp personas/ayu.yaml backups/phase1_before/
```

### Step 2: yana.yaml の修正

**作業順序**:
1. ✅ Few-shot examples を短縮（修正1）
2. ✅ deep_values セクションを追加
   - core_belief
   - emotional_state（excited, confident, worried, impatient, focused, curious）
   - decision_priority
   - quick_rules
3. 既存の system_prompt と values セクションは保持
4. YAML構文チェック

**最終的な構造**:
```yaml
name: "やな"
role: "姉 / Edge AI"
character_type: "intuitive_action_oriented"

core_identity:
  # ... 既存のまま

speaking_style:
  # ... 既存のまま

values:
  # ... 既存のまま（将来的にdeep_valuesと統合検討）

deep_values:  # ← 新規追加
  core_belief: "動かしてみないとわからない"
  emotional_state:
    excited: { ... }
    confident: { ... }
    worried: { ... }
    impatient: { ... }
    focused: { ... }
    curious: { ... }
  decision_priority: { ... }
  quick_rules: [ ... ]

system_prompt: |
  # ... 既存のまま

generation:
  # ... 既存のまま

few_shot_examples:  # ← 修正（短縮）
  - user: "JetRacerって何？"
    assistant: "自律走行車だよ！..."  # 短縮版
  # ...

metadata:
  # ... 既存のまま
```

### Step 3: ayu.yaml の修正

**作業順序**:
1. ✅ supportive Few-shot を追加（修正4）
2. ✅ deep_values セクションを追加
   - core_belief
   - emotional_state（analytical, supportive, concerned, proud, focused）
   - decision_priority
   - quick_rules
3. 既存セクションは保持
4. YAML構文チェック

### Step 4: YAML構文チェック

```bash
# Pythonで構文チェック
python -c "
import yaml
with open('personas/yana.yaml') as f:
    y = yaml.safe_load(f)
    print('yana.yaml: OK')
    print(f'  Keys: {list(y.keys())}')
    print(f'  Deep Values Keys: {list(y[\"deep_values\"].keys())}')
"

python -c "
import yaml
with open('personas/ayu.yaml') as f:
    a = yaml.safe_load(f)
    print('ayu.yaml: OK')
    print(f'  Keys: {list(a.keys())}')
    print(f'  Deep Values Keys: {list(a[\"deep_values\"].keys())}')
"
```

### Step 5: character.py への機能追加

**ファイル**: `core/character.py`

**追加するメソッド**:

```python
# ===== Deep Values関連メソッド =====

def detect_emotional_state(self, context: dict) -> str:
    """
    文脈から感情状態を判定
    
    Args:
        context: {
            'last_result': 'success' | 'failure' | None,
            'difficulty': 'low' | 'medium' | 'high',
            'yana_confidence': float (0.0-1.0),
            'ayu_confidence': float (0.0-1.0),
            'data_available': bool,
            'risk_level': float (0.0-1.0),
            'situation_type': 'normal' | 'unknown' | 'critical',
            ...
        }
    
    Returns:
        感情状態名（例: 'excited', 'analytical'）
    """
    deep_values = self.config.get('deep_values', {})
    emotional_states = deep_values.get('emotional_state', {})
    
    # 各状態のトリガーをチェック
    for state_name, state_def in emotional_states.items():
        triggers = state_def.get('triggers', [])
        
        if self._check_triggers(triggers, context):
            return state_name
    
    # デフォルト状態
    if self.name == 'yana':
        return 'confident'
    else:
        return 'analytical'

def _check_triggers(self, triggers: List[str], context: dict) -> bool:
    """
    トリガー条件のチェック
    
    Args:
        triggers: トリガー条件のリスト（例: ['success', 'high_difficulty']）
        context: 現在の状況
    
    Returns:
        トリガーが発火したかどうか
    """
    # トリガー条件の文字列を実際の条件にマッピング
    trigger_checks = {
        # 成功・失敗
        'unexpected_success': lambda c: c.get('last_result') == 'success' and c.get('difficulty') == 'high',
        'success': lambda c: c.get('last_result') == 'success',
        'failure': lambda c: c.get('last_result') == 'failure',
        
        # 状況
        'familiar_situation': lambda c: c.get('situation_type') == 'normal',
        'unknown_situation': lambda c: c.get('situation_type') == 'unknown',
        'difficult_corner': lambda c: c.get('situation_type') == 'critical',
        'high_speed_section': lambda c: c.get('speed', 0) > 2.5,
        
        # データ・分析
        'data_available': lambda c: c.get('data_available', False),
        'clear_pattern_found': lambda c: c.get('pattern_confidence', 0) > 0.8,
        
        # キャラクター状態
        'yana_failed': lambda c: c.get('last_result') == 'failure' and self.name == 'ayu',
        'yana_worried': lambda c: c.get('yana_confidence', 1.0) < 0.4,
        'high_risk_detected': lambda c: c.get('risk_level', 0) > 0.6,
        
        # デフォルト（常にTrue）
        'normal_operation': lambda c: True,
    }
    
    # いずれかのトリガーが発火すればTrue
    for trigger in triggers:
        check_func = trigger_checks.get(trigger)
        if check_func and check_func(context):
            return True
    
    return False

def build_deep_values_prompt(self, emotional_state: str) -> str:
    """
    Deep Values を元にプロンプト生成
    
    Args:
        emotional_state: 現在の感情状態
    
    Returns:
        Deep Valuesのテキスト表現
    """
    deep_values = self.config.get('deep_values', {})
    state_def = deep_values.get('emotional_state', {}).get(emotional_state, {})
    
    # プロンプトテキスト生成
    lines = [
        "【判断基準】",
        f"コアビリーフ: {deep_values.get('core_belief', '未定義')}",
        "",
        f"現在の感情状態: {emotional_state}",
        "行動パターン:"
    ]
    
    for behavior in state_def.get('behavior', []):
        lines.append(f"  - {behavior}")
    
    lines.append("")
    lines.append("判断優先度:")
    priorities = deep_values.get('decision_priority', {})
    for key, value in priorities.items():
        lines.append(f"  - {key}: {value}")
    
    lines.append("")
    lines.append("クイックルール:")
    for rule in deep_values.get('quick_rules', []):
        lines.append(f"  - {rule}")
    
    return "\n".join(lines)

def get_temperature_modifier(self, emotional_state: str) -> float:
    """
    感情状態に応じた温度調整値を取得
    
    Args:
        emotional_state: 感情状態
    
    Returns:
        温度調整値（デフォルトの温度に対する乗数）
    """
    deep_values = self.config.get('deep_values', {})
    state_def = deep_values.get('emotional_state', {}).get(emotional_state, {})
    
    # temperature_modifierが定義されていればそれを使用
    # なければデフォルトの温度をそのまま使用（modifier=1.0）
    return state_def.get('temperature_modifier', 1.0)
```

### Step 6: ユニットテスト作成

**ファイル**: `tests/test_character_deep_values.py`

```python
import pytest
from core.character import Character

# テストデータ
@pytest.fixture
def yana_config():
    import yaml
    with open('personas/yana.yaml') as f:
        return yaml.safe_load(f)

@pytest.fixture
def ayu_config():
    import yaml
    with open('personas/ayu.yaml') as f:
        return yaml.safe_load(f)

# ===== やな（姉）のテスト =====

def test_yana_emotional_state_excited(yana_config):
    """やなの興奮状態判定"""
    character = Character("yana", yana_config)
    
    context = {
        'last_result': 'success',
        'difficulty': 'high',
        'yana_confidence': 0.9
    }
    
    state = character.detect_emotional_state(context)
    assert state == 'excited'

def test_yana_emotional_state_worried(yana_config):
    """やなの心配状態判定"""
    character = Character("yana", yana_config)
    
    context = {
        'situation_type': 'unknown',
        'yana_confidence': 0.3
    }
    
    state = character.detect_emotional_state(context)
    assert state == 'worried'

def test_yana_deep_values_prompt_generation(yana_config):
    """やなのDeep Valuesプロンプト生成"""
    character = Character("yana", yana_config)
    prompt = character.build_deep_values_prompt('excited')
    
    assert "コアビリーフ" in prompt
    assert "動かしてみないとわからない" in prompt
    assert "excited" in prompt or "興奮" in prompt
    assert "判断優先度" in prompt

def test_yana_temperature_modifier(yana_config):
    """やなの温度調整"""
    character = Character("yana", yana_config)
    
    # excited時は0.9
    modifier = character.get_temperature_modifier('excited')
    assert modifier == 0.9
    
    # focused時は0.5
    modifier = character.get_temperature_modifier('focused')
    assert modifier == 0.5

# ===== あゆ（妹）のテスト =====

def test_ayu_emotional_state_supportive(ayu_config):
    """あゆのサポート状態判定"""
    character = Character("ayu", ayu_config)
    
    context = {
        'last_result': 'failure',
        'yana_confidence': 0.3
    }
    
    state = character.detect_emotional_state(context)
    assert state == 'supportive'

def test_ayu_emotional_state_concerned(ayu_config):
    """あゆの心配状態判定"""
    character = Character("ayu", ayu_config)
    
    context = {
        'risk_level': 0.7,
        'yana_confidence': 0.8  # やなは自信満々
    }
    
    state = character.detect_emotional_state(context)
    assert state == 'concerned'

def test_ayu_deep_values_prompt_generation(ayu_config):
    """あゆのDeep Valuesプロンプト生成"""
    character = Character("ayu", ayu_config)
    prompt = character.build_deep_values_prompt('analytical')
    
    assert "コアビリーフ" in prompt
    assert "データは嘘をつかない" in prompt
    assert "判断優先度" in prompt

# ===== 整合性テスト =====

def test_decision_priority_contrast(yana_config, ayu_config):
    """やなとあゆの判断優先度の対比"""
    yana_priorities = yana_config['deep_values']['decision_priority']
    ayu_priorities = ayu_config['deep_values']['decision_priority']
    
    # やなは直感重視、あゆはデータ重視
    assert yana_priorities['intuition'] > ayu_priorities['intuition']
    assert ayu_priorities['data'] > yana_priorities['data']
    
    # やなはスピード重視、あゆは正確性重視
    assert yana_priorities['speed'] > ayu_priorities['speed']
    assert ayu_priorities['accuracy'] > yana_priorities['accuracy']

def test_emotional_states_defined(yana_config, ayu_config):
    """必須の感情状態が定義されているか"""
    required_yana_states = ['excited', 'confident', 'worried', 'impatient', 'focused', 'curious']
    required_ayu_states = ['analytical', 'supportive', 'concerned', 'proud', 'focused']
    
    yana_states = list(yana_config['deep_values']['emotional_state'].keys())
    ayu_states = list(ayu_config['deep_values']['emotional_state'].keys())
    
    for state in required_yana_states:
        assert state in yana_states, f"やなに{state}状態が未定義"
    
    for state in required_ayu_states:
        assert state in ayu_states, f"あゆに{state}状態が未定義"
```

### Step 7: テスト実行

```bash
# 個別テスト実行
pytest tests/test_character_deep_values.py -v

# 全テスト実行（既存テストが壊れていないか確認）
pytest tests/ -v

# カバレッジ付きテスト
pytest tests/test_character_deep_values.py --cov=core.character --cov-report=term-missing
```

---

## ✅ 完了確認チェックリスト

### ファイル修正完了

- [ ] `personas/yana.yaml` 修正完了
  - [ ] Few-shot examples 短縮
  - [ ] deep_values セクション追加（6状態）
  - [ ] YAML構文エラーなし
  
- [ ] `personas/ayu.yaml` 修正完了
  - [ ] supportive Few-shot追加
  - [ ] deep_values セクション追加（5状態）
  - [ ] YAML構文エラーなし

### コード実装完了

- [ ] `core/character.py` にメソッド追加
  - [ ] `detect_emotional_state()`
  - [ ] `_check_triggers()`
  - [ ] `build_deep_values_prompt()`
  - [ ] `get_temperature_modifier()`

### テスト完了

- [ ] `tests/test_character_deep_values.py` 作成
  - [ ] やなのテスト（4個）
  - [ ] あゆのテスト（3個）
  - [ ] 整合性テスト（2個）
  
- [ ] 全テストが合格
  - [ ] 新規テスト: 9個全て合格
  - [ ] 既存テスト: 壊れていない

### 動作確認

- [ ] chat.py で実際に会話テスト
  - [ ] やなの応答が短くなっている
  - [ ] Deep Valuesが適用されている（ログ確認）
  - [ ] 既存機能が動作している

### ドキュメント更新

- [ ] `docs/09_実装完了レビュー報告書.md` 更新
  - [ ] Phase 1完了を記録
  - [ ] 変更内容を記録
  - [ ] テスト結果を記録

---

## 🚨 トラブルシューティング

### 問題1: YAML構文エラー

**症状**: `yaml.safe_load()` でエラー

**原因**: インデント不正、予約語の誤用

**対処**:
```bash
# オンラインYAMLバリデータでチェック
# または
python -c "import yaml; yaml.safe_load(open('personas/yana.yaml'))"
```

### 問題2: 既存テストが失敗

**症状**: pytest で既存テストがFAIL

**原因**: character.py の変更が既存機能に影響

**対処**:
1. エラーメッセージを確認
2. 変更した部分を一時的に元に戻す
3. 段階的に変更を適用

### 問題3: Deep Values が適用されない

**症状**: 応答がDeep Valuesを反映しない

**原因**: プロンプトに注入されていない

**対処**:
```python
# デバッグ用にプロンプトを出力
print(character.build_deep_values_prompt('excited'))
```

---

## 📚 参考資料

- **詳細設計書**: `docs/PERSONA_ENHANCEMENT_DESIGN_V2.md`
- **整合性チェック**: `docs/CONSISTENCY_CHECK_MATRIX.md`
- **既存実装**: `docs/09_実装完了レビュー報告書.md`

---

**作成者**: Tsuyoshi (with Claude Sonnet 4.5)  
**最終更新**: 2026年1月15日  
**推定作業時間**: 4-6時間（修正 + 実装 + テスト）
