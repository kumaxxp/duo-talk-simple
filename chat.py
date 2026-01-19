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
from core.duo_dialogue import DuoDialogueManager
from core.conversation_logger import ConversationLogger


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
    prompt_assets = dict(config.get("prompt_assets", {}))

    for char_name, char_config in char_configs.items():
        if char_config.get("enabled", True):
            char_assets = dict(prompt_assets)
            char_assets.update(char_config.get("assets", {}))
            characters[char_name] = Character(
                name=char_name,
                config_path=char_config["config"],
                ollama_client=client,
                rag_engine=rag,
                generation_defaults=char_config.get("generation", {}),
                assets=char_assets,
                max_history=char_config.get("max_history", 10),
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


def run_duo_dialogue(
    characters: dict, config: dict, topic: str, conv_logger: ConversationLogger = None
):
    """AI同士対話モードを実行"""
    logger = logging.getLogger(__name__)

    if "yana" not in characters or "ayu" not in characters:
        print("エラー: やなとあゆ両方が必要です")
        return

    # DuoDialogueManager設定
    duo_config = config.get("duo_dialogue", {})
    manager = DuoDialogueManager(
        yana=characters["yana"],
        ayu=characters["ayu"],
        config={
            "max_turns": duo_config.get("max_turns", 10),
            "first_speaker": duo_config.get("first_speaker", "yana"),
        }
    )

    # 対話開始
    print("\n" + "=" * 50)
    print("=== AI姉妹対話モード ===")
    print(f"お題: {topic}")
    print("=" * 50)

    manager.start_dialogue(topic)

    # 対話ループ
    typing_delay = duo_config.get("typing_delay", 0.5)
    show_turn_count = duo_config.get("show_turn_count", True)

    import time

    while manager.should_continue():
        try:
            speaker, response = manager.next_turn()

            # ターン表示
            if show_turn_count:
                print(f"\n[Turn {manager.turn_count}/{manager.max_turns}] {speaker}:")
            else:
                print(f"\n[{speaker}]:")

            print(response)

            # タイピング遅延
            time.sleep(typing_delay)

            # ユーザー介入チェック（Ctrl+C で中断可能）

        except KeyboardInterrupt:
            print("\n\n--- 対話を中断しました ---")
            break
        except Exception as e:
            logger.error(f"対話中にエラー: {e}")
            print(f"\nエラー: {e}")
            break

    # 対話終了
    print("\n" + "=" * 50)
    print("=== 対話終了 ===")
    print("=" * 50)

    # サマリー表示
    summary = None
    if manager.dialogue_history:
        summary = manager.get_summary()
        print("\n【対話まとめ】")
        print(summary)

    # 会話ログに記録
    if conv_logger:
        conv_logger.log_duo_dialogue(topic, manager.dialogue_history, summary)

    # 履歴をクリア（次の通常会話に影響しないように）
    characters["yana"].clear_history()
    characters["ayu"].clear_history()


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

    # 会話ログ初期化
    conv_log_config = config.get("conversation_log", {})
    conv_logger = None
    if conv_log_config.get("enabled", True):
        conv_logger = ConversationLogger(
            log_dir=conv_log_config.get("log_dir", "./logs/conversations")
        )
        conv_logger.start_session(char_names[current_char_idx])
        logger.info(f"会話ログ開始: {conv_logger.current_log_path}")

    # デバッグモード
    dev_config = config.get("development", {})
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
                    if conv_logger:
                        log_path = conv_logger.end_session()
                        print(f"会話ログ保存: {log_path}")
                    print("さようなら!")
                    break

                elif command == "/switch":
                    # 次のキャラクターに切り替え
                    current_char_idx = (current_char_idx + 1) % len(char_names)
                    new_char = char_names[current_char_idx]
                    print(f"キャラクター切り替え: {new_char}")
                    if conv_logger:
                        conv_logger.log_command("/switch", f"-> {new_char}")
                    continue

                elif command == "/clear":
                    characters[current_char].clear_history()
                    print("会話履歴をクリアしました")
                    if conv_logger:
                        conv_logger.log_command("/clear")
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
                    print("  /duo <お題> - AI姉妹対話モード")
                    print("  /debug  - RAGデバッグ表示切替")
                    print("  /exit   - 終了")
                    if conv_logger:
                        print(f"\n会話ログ: {conv_logger.current_log_path}")
                    continue

                elif user_input.lower().startswith("/duo "):
                    # AI姉妹対話モード
                    topic = user_input[5:].strip()
                    if not topic:
                        print("使い方: /duo <お題>")
                        print("例: /duo JetRacerのセンサー配置を改善したい")
                        continue
                    if conv_logger:
                        conv_logger.log_command("/duo", topic)
                    run_duo_dialogue(characters, config, topic, conv_logger)
                    continue

                elif command == "/duo":
                    print("使い方: /duo <お題>")
                    print("例: /duo JetRacerのセンサー配置を改善したい")
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

            # 会話ログ記録
            if conv_logger:
                conv_logger.log_message("user", user_input)
                conv_logger.log_message("assistant", response, character=current_char)

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
            if conv_logger:
                log_path = conv_logger.end_session()
                print(f"\n会話ログ保存: {log_path}")
            print("\n中断されました。さようなら!")
            break
        except EOFError:
            if conv_logger:
                log_path = conv_logger.end_session()
                print(f"\n会話ログ保存: {log_path}")
            print("\nさようなら!")
            break
        except Exception as e:
            logger.error(f"エラー: {e}")
            print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
