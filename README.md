# ODIADEV-TTS

Text-to-Speech service with DIA-1.6B model, FastAPI backend, and Next.js frontend.

## Project Structure

```
/odia-tts
  /backend
  /frontend
  /infra
  /scripts
  README.md
```

## Quick Start

1. **Setup Environment**:
   - Copy `/infra/env.example` to `.env` and fill in values
   - Apply `/infra/seed.sql` to your Supabase project
   - Generate an API key in your Supabase project

2. **Run with Docker**:
   ```bash
   cd infra
   docker-compose up
   ```

3. **Run locally**:
   ```bash
   cd scripts
   ./run_local.sh
   ```

## Services

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs