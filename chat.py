#!/usr/bin/env python3
# chat.py
# duo-talk-simple メインCLI

import yaml
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine
from core.character import Character


def setup_logging(config: dict) -> logging.Logger:
    """ロギング設定"""
    log_config = config.get("logging", {})

    # ルートロガー設定
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_config.get("level", "INFO")))

    # フォーマッター
    formatter = logging.Formatter(
        log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # ファイルハンドラー
    file_config = log_config.get("file", {})
    if file_config.get("enabled", False):
        log_path = file_config.get("path", "./logs/duo-talk.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=file_config.get("max_bytes", 10485760),
            backupCount=file_config.get("backup_count", 5),
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # コンソールハンドラー
    console_config = log_config.get("console", {})
    if console_config.get("enabled", True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            getattr(logging, console_config.get("level", "INFO"))
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def load_config(config_path: str = "config.yaml") -> dict:
    """設定ファイル読み込み"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def initialize_system(config: dict) -> dict:
    """システム初期化"""
    logger = logging.getLogger(__name__)

    # OllamaClient初期化
    ollama_config = config["ollama"]
    client = OllamaClient(
        base_url=ollama_config["base_url"],
        model=ollama_config["llm_model"],
        timeout=ollama_config.get("timeout", 30.0),
        max_retries=ollama_config.get("max_retries", 3),
    )

    # Ollama接続確認
    if not client.is_healthy():
        logger.error("Ollamaに接続できません。Ollamaが起動しているか確認してください。")
        sys.exit(1)

    logger.info("Ollama接続OK")

    # RAGEngine初期化
    rag_config = config["rag"]
    rag = RAGEngine(
        ollama_client=client,
        chroma_path=rag_config["chroma_db_path"],
        collection_name=rag_config["collection_name"],
    )

    # 知識ベース初期化
    knowledge_config = config["knowledge"]
    if knowledge_config.get("auto_initialize", True):
        metadata_mapping = {
            item["file"]: item["metadata"]
            for item in knowledge_config["sources"]
        }
        rag.init_from_files(
            knowledge_config["source_dir"],
            metadata_mapping,
        )

    # キャラクター初期化
    characters = {}
    char_configs = config["characters"]

    for char_name, char_config in char_configs.items():
        if char_config.get("enabled", True):
            characters[char_name] = Character(
                name=char_name,
                config_path=char_config["config"],
                ollama_client=client,
                rag_engine=rag,
            )
            logger.info(f"キャラクター「{char_name}」初期化完了")

    return {
        "client": client,
        "rag": rag,
        "characters": characters,
    }


def print_welcome(config: dict):
    """ウェルカムメッセージ表示"""
    ui_config = config.get("ui", {})
    message = ui_config.get("welcome_message", "=== duo-talk-simple ===")
    print(message)


def main():
    """メインループ"""
    # 設定読み込み
    config = load_config()

    # ロギング設定
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # システム初期化
    logger.info("システム初期化中...")
    system = initialize_system(config)
    characters = system["characters"]

    # キャラクターリスト
    char_names = list(characters.keys())
    if not char_names:
        logger.error("有効なキャラクターがありません")
        sys.exit(1)

    # 初期キャラクター（やな）
    current_char_idx = 0
    if "yana" in char_names:
        current_char_idx = char_names.index("yana")

    # デバッグモード
    dev_config = config.get("development", {})
    debug_mode = dev_config.get("debug_mode", False)
    show_rag = dev_config.get("show_rag_results", False)

    # ウェルカムメッセージ
    print_welcome(config)
    print(f"\n現在のキャラクター: {char_names[current_char_idx]}")
    print("-" * 40)

    # メインループ
    while True:
        try:
            current_char = char_names[current_char_idx]
            user_input = input(f"\n[You] > ").strip()

            if not user_input:
                continue

            # コマンド処理
            if user_input.startswith("/"):
                command = user_input.lower()

                if command == "/exit" or command == "/quit":
                    print("さようなら!")
                    break

                elif command == "/switch":
                    # 次のキャラクターに切り替え
                    current_char_idx = (current_char_idx + 1) % len(char_names)
                    print(f"キャラクター切り替え: {char_names[current_char_idx]}")
                    continue

                elif command == "/clear":
                    characters[current_char].clear_history()
                    print("会話履歴をクリアしました")
                    continue

                elif command == "/status":
                    print(f"現在のキャラクター: {current_char}")
                    print(f"会話履歴: {len(characters[current_char].history)}メッセージ")
                    continue

                elif command == "/help":
                    print("コマンド一覧:")
                    print("  /switch - キャラクター切り替え")
                    print("  /clear  - 会話履歴クリア")
                    print("  /status - 状態表示")
                    print("  /debug  - RAGデバッグ表示切替")
                    print("  /exit   - 終了")
                    continue

                elif command == "/debug":
                    show_rag = not show_rag
                    status = "ON" if show_rag else "OFF"
                    print(f"RAGデバッグ表示: {status}")
                    continue

                else:
                    print(f"不明なコマンド: {command}")
                    print("/help でコマンド一覧を表示")
                    continue

            # 応答生成
            character = characters[current_char]
            response = character.respond(user_input)

            # 応答表示
            ui_config = config.get("ui", {})
            if ui_config.get("show_character_name", True):
                print(f"\n[{current_char}] {response}")
            else:
                print(f"\n{response}")

            # RAGデバッグ表示
            if show_rag and character.last_rag_results:
                print("\n" + "=" * 40)
                print("[RAG検索結果]")
                for i, result in enumerate(character.last_rag_results, 1):
                    score = result.get("score", 0)
                    text = result.get("text", "")[:100]
                    source = result.get("metadata", {}).get("source", "不明")
                    print(f"  {i}. スコア: {score:.3f} | ソース: {source}")
                    print(f"     {text}...")
                print("=" * 40)

        except KeyboardInterrupt:
            print("\n\n中断されました。さようなら!")
            break
        except EOFError:
            print("\n\nさようなら!")
            break
        except Exception as e:
            logger.error(f"エラー: {e}")
            print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
