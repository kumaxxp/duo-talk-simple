# Architecture Codemap

**Generated**: 2026-01-19
**Freshness**: Current (Phase 5 Director/NoveltyGuard integration complete)

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
│                   │  │ - next_turn_  │  │                     │
│                   │  │   with_       │  │                     │
│                   │  │   quality_    │  │                     │
│                   │  │   check() ★5 │  │                     │
└─────────┬─────────┘  └───────┬───────┘  └─────────────────────┘
          │                    │
          │     ┌──────────────┤
          │     │              │
          ▼     ▼              ▼
┌───────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│   OllamaClient    │  │  RAGEngine    │  │  PromptBuilder      │
│ (ollama_client.py)│  │(rag_engine.py)│  │ (prompt_builder.py) │
│                   │  │               │  │                     │
│ - generate()      │  │ - search()    │  │ - load_persona()    │
│ - embed()         │  │ - add_        │  │ - build_system_     │
│ - is_healthy()    │  │   knowledge() │  │   prompt()          │
│ - set_model()     │  │ - init_from_  │  │ - guess_state()     │
│ - get_model()     │  │   files()     │  │ - select_few_shot() │
│                   │  │ - extract_    │  │                     │
│                   │  │   perspective │  │                     │
└───────────────────┘  └───────────────┘  └─────────────────────┘
          │                    │
          │     ┌──────────────┘
          ▼     ▼
┌───────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│     Ollama        │  │   ChromaDB    │  │  Quality Control ★5│
│   (External)      │  │  (External)   │  │                     │
└───────────────────┘  └───────────────┘  │ ┌─────────────────┐ │
                                          │ │    Director     │ │
                                          │ │ (director.py)   │ │
                                          │ │ - evaluate_     │ │
                                          │ │   response()    │ │
                                          │ │ - _check_*()    │ │
                                          │ │ - _score_with_  │ │
                                          │ │   llm()         │ │
                                          │ └─────────────────┘ │
                                          │ ┌─────────────────┐ │
                                          │ │  NoveltyGuard   │ │
                                          │ │(novelty_guard.py│ │
                                          │ │ - check_and_    │ │
                                          │ │   update()      │ │
                                          │ │ - _select_      │ │
                                          │ │   strategy()    │ │
                                          │ └─────────────────┘ │
                                          └─────────────────────┘
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
├── core.director.Director
├── core.novelty_guard.NoveltyGuard
├── core.types (DirectorStatus)
└── (uses Character via injection)

core/director.py
├── yaml
├── re
├── core.types (DirectorStatus, DirectorEvaluation)
└── (uses OllamaClient via injection for LLM scoring)

core/novelty_guard.py
├── enum
├── dataclasses
├── yaml
├── re
└── core.types (LoopCheckResult)

core/types.py
├── dataclasses
└── enum

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
| character.py | 175 | Character response generation |
| duo_dialogue.py | 462 | AI-to-AI dialogue orchestration, quality control integration |
| prompt_builder.py | 261 | System prompt construction |
| rag_engine.py | 299 | Vector search & knowledge management |
| ollama_client.py | 155 | LLM API interaction, model switching |
| conversation_logger.py | 156 | Conversation persistence |
| **types.py** | 41 | Shared type definitions (DirectorStatus, etc.) |
| **director.py** | 605 | Quality evaluation, static checks, LLM scoring |
| **novelty_guard.py** | 272 | Loop detection, escape strategy injection |

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
├── test_ollama_client.py        → core/ollama_client.py (13 tests)
├── test_rag_engine.py           → core/rag_engine.py (14 tests)
├── test_character.py            → core/character.py (12 tests)
├── test_prompt_builder.py       → core/prompt_builder.py (4 tests)
├── test_duo_dialogue.py         → core/duo_dialogue.py (34 tests)
├── test_conversation_logger.py  → core/conversation_logger.py (16 tests)
├── test_knowledge_perspectives  → knowledge/*.txt (11 tests)
├── test_director.py             → core/director.py (53 tests) ★Phase 1-4
├── test_novelty_guard.py        → core/novelty_guard.py (27 tests) ★Phase 2
├── test_integration.py          → Full system integration (5 tests)
├── test_performance.py          → Performance benchmarks (5 tests)
└── test_e2e_cli.py              → chat.py E2E (12 tests)
```

**Overall Coverage**: 91% (206 tests)
