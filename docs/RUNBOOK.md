# Operations Runbook (RUNBOOK.md)

**Last Updated**: 2026-01-19
**Source of Truth**: config.yaml

---

## System Overview

duo-talk-simple is a CLI application for AI character conversations.

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI | Python | User interface |
| LLM | Ollama (gemma3:12b default) | Text generation |
| Embeddings | Ollama (mxbai-embed-large) | Vector search |
| Vector DB | ChromaDB | RAG storage |
| Logging | Python logging | System logs |

### Available Models

| Preset | Model | VRAM | Use Case |
|--------|-------|------|----------|
| gemma | gemma3:12b | 8.1GB | Default, balanced |
| swallow | Swallow 8B | 4.9GB | Japanese-focused |
| cydonia | Cydonia 22B | 13.0GB | Creative roleplay |

Switch models with `/model <preset>` command.

---

## Deployment

### Prerequisites

1. Python 3.12+ installed
2. Ollama installed and running
3. Sufficient VRAM (12GB+ recommended)

### Deployment Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd duo-talk-simple

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull Ollama models
ollama pull gemma3:12b
ollama pull mxbai-embed-large

# 5. Verify setup
pytest tests/ -v -m "not slow"

# 6. Start application
python chat.py
```

### Configuration

Edit `config.yaml` for environment-specific settings:

```yaml
# Production settings
logging:
  level: "INFO"
  file:
    enabled: true

development:
  debug_mode: false
  show_prompts: false
```

---

## Monitoring

### Log Locations

| Log | Path | Purpose |
|-----|------|---------|
| System | `./logs/duo-talk.log` | Application logs |
| Conversations | `./logs/conversations/` | User conversation logs |

### Log Rotation

Configured in `config.yaml`:

```yaml
logging:
  file:
    max_bytes: 10485760  # 10MB
    backup_count: 5
```

### Health Check

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check if application can start
python -c "from core.ollama_client import OllamaClient; c = OllamaClient(); print('OK' if c.is_healthy() else 'FAIL')"
```

### Performance Metrics

```bash
# Run performance tests
pytest tests/test_performance.py -v -s
```

Expected response times:
- Basic response: < 5s
- RAG-enhanced response: < 10s
- Embedding generation: < 2s

---

## Common Issues and Fixes

### Issue: Ollama Connection Failed

**Symptoms:**
```
エラー: Ollamaに接続できません
```

**Diagnosis:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags
```

**Fix:**
```bash
# Start Ollama
ollama serve

# Or restart
pkill ollama && ollama serve
```

---

### Issue: Model Not Found

**Symptoms:**
```
Error: model 'gemma3:12b' not found
```

**Fix:**
```bash
# Pull the default model
ollama pull gemma3:12b

# Or pull alternative models
ollama pull hf.co/mmnga/tokyotech-llm-Llama-3.1-Swallow-8B-Instruct-v0.3-gguf:Q4_K_M

# Verify
ollama list

# Switch model in CLI
/model swallow
```

---

### Issue: VRAM Exceeded

**Symptoms:**
- Slow responses
- Out of memory errors

**Diagnosis:**
```bash
# Check GPU memory
nvidia-smi
```

**Fix:**
1. Use smaller model:
   ```yaml
   # config.yaml
   ollama:
     llm_model: "gemma3:4b"  # Smaller model
   ```

2. Reduce max_tokens:
   ```yaml
   characters:
     yana:
       generation:
         max_tokens: 1000  # Reduced
   ```

---

### Issue: RAG Search Returns Empty

**Symptoms:**
- No context in responses
- Technical questions not answered

**Diagnosis:**
```bash
# Check ChromaDB
ls -la ./data/chroma_db/
```

**Fix:**
```yaml
# config.yaml - Force reinitialize
knowledge:
  force_reload: true
```

Then restart the application.

---

### Issue: Test Failures

**Symptoms:**
```
FAILED tests/test_xxx.py
```

**Diagnosis:**
```bash
# Run with verbose output
pytest tests/test_xxx.py -v -s --tb=long
```

**Common Fixes:**
1. Ollama not running → Start Ollama
2. Timeout → Increase timeout in test
3. Model changed → Update test expectations

---

## Maintenance Procedures

### Daily Tasks

- [ ] Check `./logs/duo-talk.log` for errors
- [ ] Verify Ollama is running

### Weekly Tasks

- [ ] Review conversation logs for quality
- [ ] Run full test suite
- [ ] Check disk space for logs

### Monthly Tasks

- [ ] Update dependencies (`pip install -r requirements.txt --upgrade`)
- [ ] Review and archive old conversation logs
- [ ] Run performance benchmarks

---

## Backup and Recovery

### Backup Targets

| Data | Path | Frequency |
|------|------|-----------|
| Configuration | `config.yaml` | On change |
| Personas | `personas/*.yaml` | On change |
| Knowledge | `knowledge/*.txt` | On change |
| ChromaDB | `./data/chroma_db/` | Weekly |
| Conversation logs | `./logs/conversations/` | Weekly |

### Backup Commands

```bash
# Create backup
tar -czvf backup_$(date +%Y%m%d).tar.gz \
  config.yaml \
  personas/ \
  patterns/ \
  knowledge/ \
  ./data/chroma_db/

# Restore backup
tar -xzvf backup_YYYYMMDD.tar.gz
```

### Recovery Procedure

1. Stop application
2. Restore backup files
3. Verify configuration
4. Start application
5. Run health check

---

## Scaling Considerations

### Current Limitations

- Single user CLI application
- Local Ollama only
- In-process ChromaDB

### Future Improvements

If scaling needed:

1. **Multi-user**: Add API layer (FastAPI)
2. **Remote LLM**: Configure remote Ollama URL
3. **Persistent DB**: Use ChromaDB server mode

---

## Security

### Sensitive Data

| Data | Location | Protection |
|------|----------|------------|
| Conversation logs | `./logs/conversations/` | File permissions |
| ChromaDB | `./data/chroma_db/` | File permissions |

### Recommendations

1. Restrict log directory permissions:
   ```bash
   chmod 700 ./logs/
   ```

2. Don't commit conversation logs:
   ```
   # .gitignore
   logs/conversations/
   ```

3. Review logs before sharing

---

## Rollback Procedures

### Quick Rollback

```bash
# If application fails after update
git stash  # Save current changes
git checkout <previous-version>
pip install -r requirements.txt
```

### Database Rollback

```bash
# If ChromaDB corrupted
rm -rf ./data/chroma_db/
# Restart application - will reinitialize
python chat.py
```

---

## Emergency Contacts

| Role | Contact | Responsibility |
|------|---------|----------------|
| Developer | - | Code issues |
| Ops | - | Infrastructure |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-19 | Added model switching documentation | - |
| 2026-01-19 | Initial runbook created | - |

---

**Document auto-generated from source of truth files**
