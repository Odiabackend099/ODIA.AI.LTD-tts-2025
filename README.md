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

3. **Run locally (Two-Lane Deployment)**:
   ```bash
   # Start Priority Lane (Pro/Biz users)
   cd scripts
   ./start_priority.sh
   
   # In another terminal, start Free Lane (Free tier users)
   cd scripts
   ./start_free.sh
   ```

4. **Run validation tests**:
   ```bash
   # Test single lane
   python scripts/final_validation.py
   
   # Test two-lane deployment
   python scripts/two_lane_validation.py
   ```

## Services

- **Priority Lane**: http://localhost:8000 (Pro/Biz users, no watermark)
- **Free Lane**: http://localhost:8001 (Free tier users, with watermark)
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs or http://localhost:8001/docs

## Two-Lane Architecture

This deployment uses a two-lane architecture to prevent free users from starving paying customers:

- **Lane A (Priority)**: Pro/Biz users with dedicated resources, no watermark, higher rate limits
- **Lane B (Free)**: Free tier users with shared resources, watermark enforced, stricter rate limits

See `ENHANCED_PROD_RUNBOOK.md` for detailed deployment instructions.