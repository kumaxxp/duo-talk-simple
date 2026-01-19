# Core Module Codemap

**Generated**: 2026-01-19 16:00
**Freshness**: Current (Phase 2A updated)

---

## Module Index

| Module | Classes | Functions | Lines |
|--------|---------|-----------|-------|
| ollama_client.py | 1 | 0 | 141 |
| rag_engine.py | 1 | 0 | 299 |
| character.py | 1 | 0 | 175 |
| prompt_builder.py | 1 | 5 | 256 |
| duo_dialogue.py | 2 | 0 | 330 |
| conversation_logger.py | 1 | 0 | 156 |

---

## core/ollama_client.py

### Class: OllamaClient

LLM and embedding generation client using OpenAI-compatible API.

```python
class OllamaClient:
    def __init__(
        base_url: str = "http://localhost:11434/v1",
        model: str = "gemma3:12b",
        timeout: float = 30.0,
        max_retries: int = 3
    )

    def is_healthy() -> bool
        # Check Ollama connection

    def generate(
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str
        # Generate text response

    def embed(text: str) -> List[float]
        # Generate embedding vector
```

**Dependencies**: openai, ollama, logging

---

## core/rag_engine.py

### Class: RAGEngine

Vector search engine using ChromaDB for knowledge retrieval.
**Phase 2A**: Added perspective extraction for character-specific knowledge.

```python
class RAGEngine:
    def __init__(
        ollama_client: OllamaClient,
        chroma_path: str = "./data/chroma_db",
        collection_name: str = "duo_knowledge"
    )

    def add_knowledge(
        texts: List[str],
        metadatas: List[Dict] = None
    ) -> None
        # Add documents to vector store

    def search(
        query: str,
        top_k: int = 3,
        filters: Optional[Dict] = None,
        character: Optional[str] = None  # ★ Phase 2A
    ) -> List[Dict]
        # Search similar documents
        # If character specified, applies extract_perspective()

    def extract_perspective(  # ★ Phase 2A
        text: str,
        character: str  # "yana" | "ayu"
    ) -> str
        # Extract character's perspective block from text
        # Markers: 【客観】【やなの視点】【あゆの視点】
        # Fallback: 客観 → original text

    def init_from_files(
        source_dir: str,
        metadata_mapping: Dict[str, Dict]
    ) -> None
        # Initialize from knowledge files

    def _chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[str]
        # Split text into chunks
```

**Dependencies**: chromadb, OllamaClient, re

---

## core/character.py

### Class: Character

Character response generator with persona-driven prompts.

```python
class Character:
    def __init__(
        name: str,
        config_path: str,
        ollama_client: OllamaClient,
        rag_engine: RAGEngine,
        generation_defaults: Dict = None,
        assets: Dict[str, str] = None,
        max_history: int = 10
    )

    # Attributes
    name: str
    history: List[Dict[str, str]]
    last_rag_results: List[Dict]
    current_state: Optional[str]
    persona: Persona
    few_shot_patterns: List[Dict]

    def respond(
        user_input: str,
        use_rag: bool = True,
        rewrite_query: bool = False
    ) -> str
        # Generate response

    def clear_history() -> None
        # Clear conversation history

    def _build_system_prompt(
        context: str,
        user_input: str
    ) -> Tuple[str, Dict]
        # Build system prompt with state

    def _rewrite_query(user_input: str) -> str
        # Rewrite query using conversation context

    def _update_history(
        user_input: str,
        response: str
    ) -> None
        # Update conversation history
```

**Dependencies**: prompt_builder, OllamaClient, RAGEngine

---

## core/prompt_builder.py

### Dataclass: Persona

Character persona definition loaded from YAML.

```python
@dataclass
class Persona:
    id: str
    callname_self: str
    callname_other: str
    identity: Dict[str, Any]
    stance_toward_sister: Dict[str, Any]
    style: Dict[str, Any]
    deep_values: Dict[str, Any]
    required_states: List[str]
    state_controls: Dict[str, Any]
```

### Functions

```python
def load_persona(yaml_path: str | Path) -> Persona
    # Load persona from YAML file

def guess_state(
    persona: Persona,
    user_text: str,
    context: Dict = None
) -> str
    # Classify emotional state from text

def load_few_shot_patterns(yaml_path: str | Path) -> List[Dict]
    # Load few-shot examples

def select_few_shot(
    patterns: List[Dict],
    persona_id: str,
    state: str
) -> Optional[str]
    # Select matching few-shot example

def build_system_prompt(
    persona: Persona,
    state: str,
    few_shot: str = None,
    rag: str = None
) -> Tuple[str, Dict]
    # Build complete system prompt

def get_character_constraints(persona_id: str) -> str
    # Get character-specific rules
```

**Dependencies**: yaml, dataclasses, pathlib

---

## core/duo_dialogue.py

### Enum: DialogueState

```python
class DialogueState(Enum):
    IDLE = auto()
    PREPARING = auto()
    DIALOGUE = auto()
    SUMMARIZING = auto()
    COMPLETED = auto()
```

### Dataclass: DuoDialogueManager

AI-to-AI dialogue orchestration.

```python
@dataclass
class DuoDialogueManager:
    # Constructor args
    yana: Character
    ayu: Character
    config: Dict[str, Any]

    # State attributes
    state: DialogueState
    topic: Optional[str]
    dialogue_history: List[Dict[str, str]]
    turn_count: int
    max_turns: int
    first_speaker: str
    convergence_keywords: List[str]

    def start_dialogue(topic: str) -> None
        # Start new dialogue session

    def next_turn() -> Tuple[str, str]
        # Execute next turn, return (speaker, response)

    def should_continue() -> bool
        # Check if dialogue should continue

    def check_convergence() -> bool
        # Detect dialogue convergence

    def get_summary() -> str
        # Generate dialogue summary

    def _get_current_speaker() -> Character
        # Determine next speaker

    def _build_context_for_speaker(speaker: Character) -> str
        # Build context prompt
```

**Dependencies**: dataclasses, enum, Character

---

## core/conversation_logger.py

### Class: ConversationLogger

Conversation persistence to text files.

```python
class ConversationLogger:
    def __init__(log_dir: str = "./logs/conversations")

    # Properties
    current_log_path: Optional[str]

    def start_session(character_name: str = "yana") -> str
        # Start new session, return session ID

    def log_message(
        role: str,
        content: str,
        character: str = None,
        metadata: Dict = None
    ) -> None
        # Log a single message

    def log_command(
        command: str,
        result: str = None
    ) -> None
        # Log a command execution

    def log_duo_dialogue(
        topic: str,
        history: List[Dict[str, str]],
        summary: str = None
    ) -> None
        # Log AI-to-AI dialogue

    def end_session() -> Optional[str]
        # End session, return log path
```

**Dependencies**: datetime, pathlib

---

## Cross-Module Dependencies

```
                    ┌─────────────────┐
                    │ prompt_builder  │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ollama_client  │◀─│    character    │─▶│   rag_engine    │
└─────────────────┘  └────────┬────────┘  └─────────────────┘
                             │                     │
                             │                     │
                             ▼                     │
                    ┌─────────────────┐            │
                    │  duo_dialogue   │────────────┘
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │conversation_log │
                    └─────────────────┘
```

---

## State Management

| Module | State Type | Persistence |
|--------|------------|-------------|
| Character | history[] | In-memory |
| DuoDialogue | dialogue_history[] | In-memory |
| ConversationLogger | _current_file | File system |
| RAGEngine | ChromaDB collection | Persistent |
