# duo-talk Persona Spec Bundle (v1.1)

このZIPは、**LLMのキャラ設定（やな・あゆ）を「仕様 → 実装」に直結**させるための統合パッケージです。

## 収録内容

- `docs/DUO_TALK_PERSONA_SPEC.md` : 統合仕様書（このZIPの中心）
- `templates/` : すぐ導入できるテンプレ群（YAML / txt / python）
  - `templates/personas/` : `yana.yaml`, `ayu.yaml`
  - `templates/patterns/` : `few_shot_patterns.yaml`
  - `templates/director/` : `director_rules.yaml`（Directorの介入ルール）
  - `templates/knowledge/` : `jetracer_tech_with_perspectives.txt`（RAG用：客観+キャラ視点）
  - `templates/src/` : `character.py`（Phase1: Deep Values を動かすための最小実装）
  - `templates/tests/` : pytest想定の最小テスト
- `sources/` : いただいた4資料（原文そのまま）

## 使い方（最短）

1) `docs/DUO_TALK_PERSONA_SPEC.md` をリポジトリの仕様書として採用
2) `templates/` をあなたの実装構成に合わせてコピー
3) `templates/tests/` をCIに入れて **「キャラ崩壊の回帰」を止める**

## 想定
- YAMLは「LLMへ注入する設定」と「Few-shotパターン」の単一ソース（SSOT）
- PythonはPhase1（Deep Values）の最小スケルトン（あなたの実装に合わせて置換OK）
