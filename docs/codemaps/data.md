# Data Models Codemap

**Generated**: 2026-01-19 18:00
**Freshness**: Current (Model switching added)

---

## Configuration Schema

### config.yaml

```yaml
# Type definitions for config.yaml

ollama:
  base_url: str          # "http://localhost:11434/v1"
  llm_model: str         # "gemma3:12b"
  embed_model: str       # "mxbai-embed-large"
  timeout: float         # 30.0
  max_retries: int       # 3

# ★ Model Presets (runtime switching via /model command)
model_presets:
  <preset_key>:          # "gemma" | "swallow" | "cydonia"
    name: str            # Ollama model identifier
    description: str     # Human-readable description
    vram_usage_gb: float # VRAM requirement

rag:
  chroma_db_path: str    # "./data/chroma_db"
  collection_name: str   # "duo_knowledge"
  top_k: int             # 3
  similarity_threshold: float  # 0.5
  chunk_size: int        # 1000
  chunk_overlap: int     # 100
  enable_query_rewrite: bool   # false
  rewrite_temperature: float   # 0.1

knowledge:
  source_dir: str        # "./knowledge"
  sources: List[KnowledgeSource]
  auto_initialize: bool  # true
  force_reload: bool     # false

KnowledgeSource:
  file: str              # "jetracer_tech.txt"
  metadata:
    domain: str          # "technical" | "character"
    character: str       # "both" | "yana" | "ayu"
    priority: str        # "high" | "medium" | "low"

prompt_assets:
  few_shot_patterns: str # "./patterns/few_shot_patterns.yaml"
  director_rules: str    # "./director/director_rules.yaml"

characters:
  <name>:                # "yana" | "ayu"
    enabled: bool
    config: str          # persona YAML path
    generation:
      temperature: float
      max_tokens: int
      top_p: float
      frequency_penalty: float
    max_history: int
    use_rag_by_default: bool

duo_dialogue:
  max_turns: int         # 10
  first_speaker: str     # "yana"
  show_turn_count: bool  # true
  typing_delay: float    # 0.5

conversation_log:
  enabled: bool          # true
  log_dir: str           # "./logs/conversations"

logging:
  level: str             # "INFO"
  format: str
  file:
    enabled: bool
    path: str
    max_bytes: int
    backup_count: int
  console:
    enabled: bool
    level: str
```

---

## Knowledge Format (Phase 2A)

### Perspective Block Format

Knowledge files can contain perspective markers for character-specific extraction:

```text
## Section Title

【客観】
- Objective fact 1
- Objective fact 2

【やなの視点】
- やな's perspective on this topic
- Action-oriented, intuitive approach

【あゆの視点】
- あゆ's perspective on this topic
- Data-driven, analytical approach
```

**Extraction Logic** (`RAGEngine.extract_perspective()`):
1. If character's perspective block exists → return that block
2. If not, fallback to 【客観】 block
3. If no markers exist → return original text

**Files Using This Format**:
- `knowledge/jetracer_tech_with_perspectives.txt` ✅
- `knowledge/jetracer_tech.txt` (Phase 2B target)
- `knowledge/sisters_shared.txt` (Phase 2B target)

---

## Persona Schema

### personas/*.yaml

```yaml
# Type definitions for persona YAML (SSOT)

id: str                  # "yana" | "ayu"
role: str                # "sister_older" | "sister_younger"
callname_self: str       # "やな" | "あゆ"
callname_other: str      # "あゆ" | "姉様"

identity:
  summary: str           # Character description
  core_belief: str       # Core value statement
  personality: List[str] # Trait keywords

stance_toward_sister:
  relationship: str      # Relationship description
  role_in_duo: str       # Role in conversation
  how_i_see_her: str     # View of sister
  attitude: List[str]    # Behavioral rules
  typical_interactions: List[str]
  typical_phrases: List[str]

style:
  register: str          # "casual" | "polite"
  tempo: str             # "fast" | "medium" | "slow"
  length: str            # "short" | "medium" | "long"
  quirks: List[str]      # Speech characteristics
  forbidden: List[str]   # Prohibited behaviors

deep_values:
  decision_priority:
    intuition: int       # 0-100
    speed: int           # 0-100
    accuracy: int        # 0-100
    safety: int          # 0-100
    empathy: int         # 0-100
    data: int            # 0-100 (ayu only)
  collaboration:
    strengths: List[str]
    asks_from_other: List[str]

required_states: List[str]  # ["excited", "confident", ...]

state_controls:
  <state>:
    temperature: float   # 0.0-1.0
    max_sentences: int   # 2-5
    tone_notes: List[str]
```

---

## Few-Shot Pattern Schema

### patterns/few_shot_patterns.yaml

```yaml
# Type definitions for few-shot patterns

items: List[FewShotPattern]

FewShotPattern:
  id: str                # "yana_excited_01"
  persona: str           # "yana" | "ayu"
  state: str             # State name
  trigger: str           # When to use
  examples: List[str]    # Example responses
```

---

## Runtime Data Structures

### Message

```python
# Conversation message format
Message = TypedDict('Message', {
    'role': str,        # "user" | "assistant" | "system"
    'content': str,     # Message text
})
```

### RAGResult

```python
# RAG search result format
RAGResult = TypedDict('RAGResult', {
    'text': str,        # Retrieved text
    'score': float,     # Similarity score (0-1)
    'metadata': Dict,   # Document metadata
})
```

### DialogueEntry

```python
# Duo dialogue turn format
DialogueEntry = TypedDict('DialogueEntry', {
    'speaker': str,     # "yana" | "ayu"
    'content': str,     # Response text
})
```

### GenerationConfig

```python
# LLM generation parameters
GenerationConfig = TypedDict('GenerationConfig', {
    'temperature': float,
    'max_tokens': int,
    'top_p': float,
    'frequency_penalty': float,
})
```

---

## Persistent Storage

### ChromaDB (Vector Store)

```
Collection: duo_knowledge
├── id: str (UUID)
├── embedding: List[float] (768 dimensions)
├── document: str (text chunk)
└── metadata:
    ├── domain: str
    ├── character: str
    ├── priority: str
    └── source: str (filename)
```

### Conversation Logs

```
logs/conversations/chat_YYYYMMDD_HHMMSS.txt
├── Header (session info)
├── Messages ([HH:MM:SS] role: content)
├── Commands ([HH:MM:SS] [CMD] command -> result)
├── Duo Dialogues (Turn-by-turn with summary)
└── Footer (session end)
```

### System Logs

```
logs/duo-talk.log
├── Timestamp
├── Logger name
├── Level (INFO/WARNING/ERROR)
└── Message
```

---

## State Definitions

### Character States (やな)

| State | Temperature | Sentences | Triggers |
|-------|-------------|-----------|----------|
| excited | 0.9 | 3 | 試, やってみ, 実験 |
| confident | 0.7 | 3 | (default success) |
| worried | 0.4 | 3 | 不安, 怖, 失敗 |
| impatient | 0.8 | 2 | 急, 早く, 今すぐ |
| focused | 0.5 | 3 | (task context) |
| curious | 0.6 | 3 | なんで, 気になる |

### Character States (あゆ)

| State | Temperature | Sentences | Triggers |
|-------|-------------|-----------|----------|
| analytical | 0.4 | 3 | 手順, 検証, データ |
| skeptical | 0.3 | 2 | やろう, 行こう |
| supportive | 0.5 | 3 | (agreement) |
| concerned | 0.3 | 3 | 危, リスク, やば |
| proud | 0.6 | 3 | ありがと, 成功 |
| focused | 0.4 | 3 | (task context) |

---

## Data Validation

| Data | Validation | Error Handling |
|------|------------|----------------|
| config.yaml | YAML parse | Exit on invalid |
| persona YAML | Schema check | Warning + defaults |
| Knowledge files | File exists | Skip missing |
| ChromaDB | Collection check | Auto-create |
| Log directory | Path exists | Auto-create |
