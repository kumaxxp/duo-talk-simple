# Architecture Codemap

**Generated**: 2026-01-19 18:00
**Freshness**: Current (Model switching added)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         chat.py (CLI)                           │
│  - setup_logging()    - load_config()    - initialize_system()  │
│  - print_welcome()    - run_duo_dialogue()    - main()          │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
┌───────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│    Character      │  │DuoDialogue    │  │ConversationLogger   │
│    (character.py) │  │Manager        │  │(conversation_       │
│                   │  │(duo_dialogue. │  │ logger.py)          │
│ - respond()       │  │ py)           │  │                     │
│ - clear_history() │  │               │  │ - start_session()   │
│                   │  │ - start_      │  │ - log_message()     │
│                   │  │   dialogue()  │  │ - log_duo_dialogue()│
│                   │  │ - next_turn() │  │ - end_session()     │
│                   │  │ - get_summary │  │                     │
└─────────┬─────────┘  └───────┬───────┘  └─────────────────────┘
          │                    │
          │     ┌──────────────┘
          │     │
          ▼     ▼
┌───────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│   OllamaClient    │  │  RAGEngine    │  │  PromptBuilder      │
│ (ollama_client.py)│  │(rag_engine.py)│  │ (prompt_builder.py) │
│                   │  │               │  │                     │
│ - generate()      │  │ - search()    │  │ - load_persona()    │
│ - embed()         │  │ - add_        │  │ - build_system_     │
│ - is_healthy()    │  │   knowledge() │  │   prompt()          │
│ - set_model() ★  │  │ - init_from_  │  │ - guess_state()     │
│ - get_model() ★  │  │   files()     │  │ - select_few_shot() │
│                   │  │ - extract_    │  │                     │
│                   │  │   perspective │  │                     │
│                   │  │   () ★2A     │  │                     │
└───────────────────┘  └───────────────┘  └─────────────────────┘
          │                    │
          ▼                    ▼
┌───────────────────┐  ┌───────────────┐
│     Ollama        │  │   ChromaDB    │
│   (External)      │  │  (External)   │
└───────────────────┘  └───────────────┘
```

---

## Dependency Graph

```
chat.py
├── core.ollama_client.OllamaClient
├── core.rag_engine.RAGEngine
├── core.character.Character
├── core.duo_dialogue.DuoDialogueManager
└── core.conversation_logger.ConversationLogger

core/character.py
├── core.prompt_builder (module)
└── (uses OllamaClient, RAGEngine via injection)

core/duo_dialogue.py
├── dataclasses
├── enum
└── (uses Character via injection)

core/prompt_builder.py
├── dataclasses
├── pathlib
└── yaml

core/rag_engine.py
├── chromadb
├── re (Phase 2A: perspective extraction)
└── (uses OllamaClient via injection)

core/ollama_client.py
├── openai (OpenAI-compatible client)
└── ollama (native client)

core/conversation_logger.py
├── datetime
└── pathlib
```

---

## Module Responsibilities

| Module | Lines | Responsibility |
|--------|-------|----------------|
| chat.py | 419 | CLI entry point, command handling, /model command |
| character.py | 173 | Character response generation |
| duo_dialogue.py | 186 | AI-to-AI dialogue orchestration |
| prompt_builder.py | 256 | System prompt construction |
| rag_engine.py | 299 | Vector search & knowledge management |
| ollama_client.py | 155 | LLM API interaction, model switching |
| conversation_logger.py | 157 | Conversation persistence |

---

## Data Flow

```
User Input
    │
    ▼
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ chat.py  │ ──▶ │ Character │ ──▶ │ RAGEngine    │
└──────────┘     │           │     │ (search)     │
                 │           │     └──────────────┘
                 │           │            │
                 │           │            ▼
                 │           │     ┌──────────────┐
                 │           │ ◀── │ Context      │
                 │           │     └──────────────┘
                 │           │
                 │           │     ┌──────────────┐
                 │           │ ──▶ │PromptBuilder │
                 │           │     │(build_prompt)│
                 │           │     └──────────────┘
                 │           │            │
                 │           │            ▼
                 │           │     ┌──────────────┐
                 │           │ ◀── │ System Prompt│
                 │           │     └──────────────┘
                 │           │
                 │           │     ┌──────────────┐
                 │           │ ──▶ │ OllamaClient │
                 │           │     │ (generate)   │
                 │           │     └──────────────┘
                 │           │            │
                 ▼           │            ▼
┌──────────┐     │           │     ┌──────────────┐
│ Response │ ◀── │           │ ◀── │ LLM Response │
└──────────┘     └───────────┘     └──────────────┘
```

---

## External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| openai | >=1.0.0 | OpenAI-compatible API |
| chromadb | >=0.4.22 | Vector database |
| pyyaml | >=6.0 | Configuration |
| ollama | - | Native Ollama client |

---

## Configuration Files

| File | Purpose |
|------|---------|
| config.yaml | Main system configuration |
| personas/yana.yaml | やな character definition |
| personas/ayu.yaml | あゆ character definition |
| patterns/few_shot_patterns.yaml | Few-shot examples |
| director/director_rules.yaml | Director intervention rules |

---

## Test Coverage Map

```
tests/
├── test_ollama_client.py    → core/ollama_client.py (87%)
├── test_rag_engine.py       → core/rag_engine.py (93%)
├── test_character.py        → core/character.py (88%)
├── test_prompt_builder.py   → core/prompt_builder.py (91%)
├── test_duo_dialogue.py     → core/duo_dialogue.py (99%)
├── test_conversation_logger → core/conversation_logger.py (98%)
├── test_integration.py      → Full system (integration)
├── test_performance.py      → Performance benchmarks
└── test_e2e_cli.py          → chat.py (E2E)
```

**Overall Coverage**: 94%
