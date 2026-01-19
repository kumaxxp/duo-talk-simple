#!/usr/bin/env python3
"""
モデル比較テストスクリプト
3つのモデル（Gemma, Swallow, Cydonia）でキャラクター応答を比較
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import time
from core.ollama_client import OllamaClient
from core.prompt_builder import load_persona, build_system_prompt, guess_state


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_model(client: OllamaClient, model_name: str, persona_path: str, test_prompt: str):
    """指定モデルでキャラクター応答をテスト"""
    client.set_model(model_name)

    # ペルソナ読み込み
    persona = load_persona(persona_path)
    state = guess_state(persona, test_prompt)
    system_prompt, gen_hints = build_system_prompt(persona, state)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": test_prompt},
    ]

    start_time = time.time()
    response = client.generate(
        messages=messages,
        temperature=gen_hints.get("temperature", 0.7),
        max_tokens=500,
    )
    elapsed = time.time() - start_time

    return response, elapsed, state


def main():
    config = load_config()

    # モデルプリセット
    presets = config.get("model_presets", {})

    # テスト設定
    test_prompts = [
        ("yana", "キャンプ行きたいな〜。あゆも一緒にどう？"),
        ("ayu", "姉様、またキャンプですか。準備は大変ですよ。"),
    ]

    # Ollama クライアント初期化
    ollama_config = config["ollama"]
    client = OllamaClient(
        base_url=ollama_config["base_url"],
        model=ollama_config["llm_model"],
        timeout=60.0,  # 比較テスト用に長めに
        max_retries=2,
    )

    print("=" * 70)
    print("モデル比較テスト")
    print("=" * 70)

    results = {}

    for preset_key, preset in presets.items():
        model_name = preset["name"]
        print(f"\n{'=' * 70}")
        print(f"モデル: {preset_key} ({preset['description']})")
        print(f"VRAM: {preset['vram_usage_gb']}GB")
        print("=" * 70)

        results[preset_key] = []

        for persona_id, prompt in test_prompts:
            persona_path = f"./personas/{persona_id}.yaml"
            print(f"\n[{persona_id}] プロンプト: {prompt}")
            print("-" * 50)

            try:
                response, elapsed, state = test_model(client, model_name, persona_path, prompt)
                print(f"状態: {state}")
                print(f"応答時間: {elapsed:.2f}秒")
                print(f"応答:\n{response}")
                results[preset_key].append({
                    "persona": persona_id,
                    "prompt": prompt,
                    "response": response,
                    "elapsed": elapsed,
                    "state": state,
                })
            except Exception as e:
                print(f"エラー: {e}")
                results[preset_key].append({
                    "persona": persona_id,
                    "prompt": prompt,
                    "error": str(e),
                })

    # サマリー出力
    print("\n" + "=" * 70)
    print("比較サマリー")
    print("=" * 70)

    for preset_key in presets:
        print(f"\n【{preset_key}】")
        for r in results.get(preset_key, []):
            if "error" in r:
                print(f"  {r['persona']}: エラー - {r['error']}")
            else:
                resp_preview = r["response"][:80].replace("\n", " ")
                print(f"  {r['persona']}: {r['elapsed']:.2f}秒 | {resp_preview}...")


if __name__ == "__main__":
    main()
