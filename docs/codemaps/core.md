# Core Module Codemap

**Generated**: 2026-01-19
**Freshness**: Current (Phase 5 Director/NoveltyGuard integration complete)

---

## Module Index

| Module | Classes | Functions | Lines |
|--------|---------|-----------|-------|
| ollama_client.py | 1 | 0 | 155 |
| rag_engine.py | 1 | 0 | 299 |
| character.py | 1 | 0 | 175 |
| prompt_builder.py | 1 | 6 | 261 |
| duo_dialogue.py | 2 | 1 | 462 |
| conversation_logger.py | 1 | 0 | 156 |
| **types.py** | 2 | 0 | 41 |
| **director.py** | 1 | 0 | 605 |
| **novelty_guard.py** | 2 | 0 | 272 |

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

    def set_model(model: str) -> None  # ★ Model switching
        # Dynamically change model

    def get_model() -> str  # ★ Model switching
        # Get current model name
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

AI-to-AI dialogue orchestration with quality control integration.

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

    # Quality control (Phase 5)
    director: Optional[Director]        # Quality evaluator
    novelty_guard: Optional[NoveltyGuard]  # Loop detector
    max_retries: int = 3

    def start_dialogue(topic: str) -> None
        # Start new dialogue session

    def next_turn() -> Tuple[str, str]
        # Execute next turn, return (speaker, response)

    def next_turn_with_quality_check() -> Tuple[str, str, Dict[str, Any]]
        # Execute turn with Director evaluation and retry
        # Returns (speaker, response, quality_info)
        # quality_info: {status, attempts, checks, novelty_check}

    def should_continue() -> bool
        # Check if dialogue should continue

    def check_convergence() -> bool
        # Detect dialogue convergence

    def get_summary() -> str
        # Generate dialogue summary

    def get_quality_report() -> Dict[str, Any]
        # Generate quality report for entire dialogue

    def _get_current_speaker() -> Character
        # Determine next speaker

    def _build_context_for_speaker(speaker: Character) -> str
        # Build context prompt
```

**Dependencies**: dataclasses, enum, Character, Director, NoveltyGuard

---

## core/types.py

### Enum: DirectorStatus

Quality evaluation result status.

```python
class DirectorStatus(Enum):
    PASS = "PASS"    # Good quality, proceed
    WARN = "WARN"    # Minor issues, accept with warning
    RETRY = "RETRY"  # Quality failure, regenerate
```

### Dataclass: DirectorEvaluation

Director evaluation result container.

```python
@dataclass
class DirectorEvaluation:
    status: DirectorStatus
    checks: dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    avg_score: float = 0.0
```

### Dataclass: LoopCheckResult

NoveltyGuard loop detection result.

```python
@dataclass
class LoopCheckResult:
    loop_detected: bool = False
    stuck_nouns: list[str] = field(default_factory=list)
    strategy: str = ""
    injection: str = ""
    consecutive_count: int = 0
```

**Dependencies**: dataclasses, enum

---

## core/director.py

### Class: Director

Quality evaluation system with static checks and LLM scoring.

```python
class Director:
    def __init__(
        rules_path: str = "director/director_rules.yaml",
        enable_static_checks: bool = True,
        enable_llm_scoring: bool = False,
        llm_client: Optional[OllamaClient] = None
    )

    # Main evaluation method
    def evaluate_response(
        speaker: str,  # "yana" | "ayu"
        response: str,
        history: list[dict[str, str]] | None = None,
        turn: int = 0
    ) -> DirectorEvaluation

    # Static checks (Phase 1)
    def _check_format(response: str) -> dict
        # Check line count, sentence count

    def _check_praise_words(response: str, speaker: str) -> dict
        # Check forbidden praise words (ayu only)

    def _check_setting_consistency(response: str) -> dict
        # Check for setting-breaking expressions

    def _check_ai_isms(response: str) -> dict
        # Check for AI-like expressions

    # Tone markers (Phase 3)
    def _check_tone_markers(speaker: str, response: str) -> dict
        # 3-signal evaluation: marker_hit + vocab_hit + style_hit
        # score >= 2 → PASS, score == 1 → WARN, score == 0 → RETRY

    # LLM scoring (Phase 4)
    def _score_with_llm(
        speaker: str,
        response: str,
        history: list[dict[str, str]],
        turn: int
    ) -> dict
        # 5-axis LLM evaluation
```

**5-Axis LLM Scoring**:
| Axis | Description |
|------|-------------|
| frame_consistency | 状況に合った内容か |
| roleplay | 姉妹の関係性が守られているか |
| connection | 相手の発言を無視していないか |
| information_density | 内容が薄すぎ/詰め込みすぎていないか |
| naturalness | 自然な表現か |

**Score Thresholds**: avg < 3.5 → RETRY / 3.5-4.0 → WARN / >= 4.0 → PASS

**Dependencies**: yaml, re, OllamaClient, types

---

## core/novelty_guard.py

### Enum: LoopBreakStrategy

Loop escape strategies.

```python
class LoopBreakStrategy(Enum):
    SPECIFIC_SLOT = "specific_slot"      # 具体的数値を要求
    CONFLICT_WITHIN = "conflict_within"  # 姉妹意見対立を促す
    ACTION_NEXT = "action_next"          # 次の行動決定を促す
    PAST_REFERENCE = "past_reference"    # 過去エピソード参照
    FORCE_WHY = "force_why"              # なぜ？で掘り下げ
    CHANGE_TOPIC = "change_topic"        # 最終手段：話題変更
```

### Class: NoveltyGuard

Loop detection and escape strategy injection.

```python
class NoveltyGuard:
    def __init__(
        window_size: int = 3,
        max_topic_depth: int = 3,
        rules_path: Optional[str] = None
    )

    def check_and_update(
        text: str,
        update: bool = True
    ) -> LoopCheckResult
        # Check for loop and optionally update state

    def extract_nouns(text: str) -> set[str]
        # Extract nouns using regex patterns

    def reset() -> None
        # Reset tracking state for new dialogue

    def get_state() -> dict
        # Get current state for inspection

    def _select_strategy() -> LoopBreakStrategy
        # Select escape strategy avoiding recent ones

    def _generate_injection(
        strategy: LoopBreakStrategy,
        stuck_nouns: list[str]
    ) -> str
        # Generate context injection text
```

**Dependencies**: enum, dataclasses, yaml, re, types

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
        │                    │                     │
        │                    │                     │
        │                    ▼                     │
        │           ┌─────────────────┐            │
        │           │  duo_dialogue   │────────────┘
        │           └────────┬────────┘
        │                    │
        │         ┌──────────┴──────────┐
        │         │                     │
        │         ▼                     ▼
        │  ┌─────────────────┐  ┌─────────────────┐
        └─▶│    director     │  │  novelty_guard  │
           └─────────────────┘  └─────────────────┘
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
| NoveltyGuard | _noun_history[], _used_strategies[] | In-memory |
| Director | - (stateless) | - |
