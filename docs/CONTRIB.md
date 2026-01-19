# Development Guide (CONTRIB.md)

**Last Updated**: 2026-01-19
**Source of Truth**: config.yaml, requirements.txt

---

## Development Environment Setup

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Runtime |
| Ollama | Latest | Local LLM |
| VRAM | 12GB+ | Model loading |

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd duo-talk-simple

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download Ollama models
ollama pull gemma3:12b
ollama pull mxbai-embed-large

# Verify installation
pytest tests/ -v --tb=short
```

---

## Dependencies

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| openai | >=1.0.0 | OpenAI-compatible API client |
| chromadb | >=0.4.22 | Vector database for RAG |
| pyyaml | >=6.0 | YAML configuration parsing |
| python-dotenv | >=1.0.0 | Environment variable loading |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=7.4.0 | Test framework |
| pytest-cov | >=4.1.0 | Coverage reporting |
| pytest-mock | >=3.12.0 | Mocking utilities |
| pexpect | >=4.9.0 | CLI E2E testing |
| black | >=23.0.0 | Code formatting |
| flake8 | >=6.0.0 | Linting |

---

## Development Workflow

### TDD (Test-Driven Development)

This project follows strict TDD methodology:

```
1. RED    - Write a failing test
2. GREEN  - Write minimal code to pass
3. REFACTOR - Improve code quality
```

### Branch Strategy

```
main
├── feature/<name>   # New features
├── fix/<name>       # Bug fixes
└── refactor/<name>  # Code improvements
```

### Commit Convention

```
<type>: <description>

Types: feat, fix, refactor, docs, test, chore
```

Examples:
```
feat: add /duo command for AI-to-AI dialogue
fix: resolve timeout in RAG search
refactor: clean dead code in chat.py
```

---

## Testing

### Test Categories

| Category | File | Description |
|----------|------|-------------|
| Unit | test_ollama_client.py | OllamaClient unit tests |
| Unit | test_rag_engine.py | RAGEngine unit tests |
| Unit | test_character.py | Character unit tests |
| Unit | test_prompt_builder.py | PromptBuilder unit tests |
| Unit | test_duo_dialogue.py | DuoDialogue unit tests |
| Unit | test_conversation_logger.py | Logger unit tests |
| Integration | test_integration.py | Full system tests |
| Performance | test_performance.py | Response time tests |
| E2E | test_e2e_cli.py | CLI interaction tests |

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov-report=html

# Fast tests only (skip LLM-heavy)
pytest tests/ -v -m "not slow"

# Specific test file
pytest tests/test_character.py -v

# Specific test
pytest tests/test_character.py::TestCharacter::test_init -v
```

### Coverage Target

- **Minimum**: 80%
- **Current**: 93%

```bash
# View coverage report
open htmlcov/index.html
```

---

## Code Quality

### Formatting

```bash
# Format code with black
black chat.py core/ tests/

# Check formatting
black --check chat.py core/ tests/
```

### Linting

```bash
# Run flake8
flake8 chat.py core/ --max-line-length=100

# Check for unused imports/variables
flake8 chat.py core/ --select=F401,F841
```

### Dead Code Analysis

```bash
# Install vulture
pip install vulture

# Run analysis
vulture chat.py core/ --min-confidence 80
```

---

## Configuration

### config.yaml Structure

```yaml
ollama:           # LLM settings
  llm_model: "gemma3:12b"
  embed_model: "mxbai-embed-large"

rag:              # RAG settings
  top_k: 3
  similarity_threshold: 0.5

knowledge:        # Knowledge base
  source_dir: "./knowledge"
  sources: [...]

characters:       # Character configs
  yana: {...}
  ayu: {...}

duo_dialogue:     # AI-to-AI dialogue
  max_turns: 10
  first_speaker: "yana"

logging:          # Logging settings
  level: "INFO"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DUO_TALK_DEBUG | Enable debug mode | false |
| DUO_TALK_LOG_LEVEL | Log level | INFO |

---

## Adding New Features

### 1. Adding a New Command

1. Add command handling in `chat.py` main loop
2. Add tests in `tests/test_e2e_cli.py`
3. Update help message in `config.yaml`
4. Update documentation

### 2. Adding a New Character State

1. Add state to `personas/<character>.yaml`:
   ```yaml
   required_states:
     - new_state
   state_controls:
     new_state:
       temperature: 0.5
       max_sentences: 3
   ```

2. Add Few-shot patterns in `patterns/few_shot_patterns.yaml`

3. Add tests:
   ```python
   def test_new_state_has_pattern(self):
       # Verify pattern exists
   ```

### 3. Adding Knowledge

1. Create file in `knowledge/`
2. Add to `config.yaml`:
   ```yaml
   knowledge:
     sources:
       - file: "new_knowledge.txt"
         metadata:
           domain: "technical"
           character: "both"
   ```

---

## Debugging

### Enable Debug Mode

```yaml
# config.yaml
development:
  debug_mode: true
  show_prompts: true
  show_rag_results: true
```

### View RAG Results

```bash
# In CLI
/debug
```

### Check Logs

```bash
# System log
tail -f logs/duo-talk.log

# Conversation logs
ls logs/conversations/
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        chat.py (CLI)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Character                              │
│  - respond()                                                │
│  - _build_system_prompt()                                   │
│  - _rewrite_query()                                         │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ OllamaClient│    │   RAGEngine      │    │  PromptBuilder  │
│  - generate()│    │  - search()      │    │  - load_persona()│
│  - embed()  │    │  - add_knowledge()│    │  - build_prompt()│
└─────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Ollama connection failed | Ollama not running | `ollama serve` |
| Model not found | Model not pulled | `ollama pull gemma3:12b` |
| VRAM exceeded | Model too large | Use smaller model |
| Tests timeout | LLM slow | Increase timeout |

### Getting Help

1. Check existing docs in `docs/`
2. Review test cases for examples
3. Check `10_改良仕様書.md` for known issues

---

**Document auto-generated from source of truth files**
