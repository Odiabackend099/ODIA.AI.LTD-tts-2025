# ODIADEV-TTS Production Runbook

**Version:** v1.2-prod-ready  
**Last Updated:** 2025-10-19  
**Author:** CROSSO Engineering Team

## 🚨 CRITICAL FIRST STEPS

### 1. Freeze the Build
```bash
git tag v1.2-prod-ready && git push origin v1.2-prod-ready
```

### 2. Verify Secrets
**Backend `.env` must contain:**
- `HF_TOKEN` (HuggingFace access token)
- `SUPABASE_SERVICE_ROLE_KEY` (Supabase admin key)
- `DIA_MODEL_ID=nari-labs/Dia-1.6B`
- `DIA_MODEL_REV=main` (pin to specific commit in production)
- `DIA_USE_BNB=0` (set to 1 for 8-bit quantization if needed)

**Frontend `.env` must contain:**
- `NEXT_PUBLIC_API_BASE=https://api.odia.dev`

### 3. Deploy to RunPod
```bash
# Start without --reload
python -m app.main

# Verify warm start
# Check logs for "DIA model loaded" and "ECAPA encoder loaded"
# Confirm VRAM usage < 14.5 GB
```

## 📊 KPIs TO MONITOR (First 7 Days)

| Metric | Target | Alert Threshold | Dashboard |
|--------|--------|----------------|-----------|
| Revenue per GPU-hour | ≥ $30/h | < $20/h | Billing |
| Cache hit rate | ≥ 40% | < 30% | Redis/Metrics |
| p50 latency | ≤ 3.5s | > 4.0s | Prometheus |
| p95 latency | < 6s | > 6s for 10min | Prometheus |
| Clone success rate | > 98% | < 95% | API Logs |
| Refunds/chargebacks | = 0 | > 0 | Stripe |

## 🚨 INCIDENT RESPONSE

### OOM (Out of Memory)
**Symptoms:** 
- 500 errors with "CUDA out of memory"
- GPU utilization 100% for >10s
- nvidia-smi showing >15.5 GB usage

**Response:**
1. Immediately switch to non-clone pool:
   ```bash
   # Set env flag to reject voice_id
   export DISABLE_VOICE_CLONING=1
   ```
2. Purge request queue
3. Roll back to v1.1-clone-enabled image
4. Notify team: `@channel OOM incident - rolling back`

### Latency Spike
**Symptoms:**
- p95 > 6s for 10+ minutes
- Queue length > 10

**Response:**
1. Scale to A10G:
   ```bash
   # In RunPod dashboard, change GPU type
   ```
2. Increase replica count if using Kubernetes
3. Monitor recovery

### Abuse/Spam
**Symptoms:**
- 10x normal request rate from single IP
- Storage usage spiking
- Billing anomaly

**Response:**
1. Block IP in Cloudflare/WAF
2. Temporarily reduce rate limits
3. Review consent records for pattern

## 🔧 OPERATIONAL COMMANDS

### Health Check
```bash
curl -s https://api.odia.dev/health | jq
```

### Metrics Endpoint
```bash
curl -s https://api.odia.dev/metrics
```

### Force Cache Clear
```bash
# Connect to Redis
redis-cli -h redis-host flushall
```

### Manual Voice Profile Cleanup
```bash
# Run cleanup script
python scripts/lifecycle_policy.py
```

### GPU Monitoring
```bash
watch -n 2 nvidia-smi
```

## 🔁 ROLLBACK PROCEDURE

### To v1.1-clone-enabled
```bash
# 1. Tag current state
git tag rollback-$(date +%s) && git push origin rollback-$(date +%s)

# 2. Switch to previous image
# In RunPod: Change image to v1.1-clone-enabled

# 3. Verify rollback
curl -s https://api.odia.dev/health | jq
```

### To v1.0-aida-stable (Emergency)
```bash
# 1. Disable voice cloning entirely
export DISABLE_VOICE_CLONING=1

# 2. Switch to v1.0 image
# In RunPod: Change image to v1.0-aida-stable

# 3. Purge queue and restart
```

## 📈 SCALING DECISIONS

### When to Scale to A10G
**Trigger:** ANY of these conditions met for 15+ minutes:
- p95 latency > 6s AFTER cache tuning
- Queue length consistently > 10
- GPU utilization > 90% for 5+ minutes

### When to Scale Horizontally
**Trigger:** 
- 100+ concurrent users
- Revenue/GPU-hr > $50 (maximize utilization)

## ⚠️ COMMON PITFALLS

1. **Forgetting `--reload` flag** - Always start without it
2. **Model revision drift** - Pin DIA_MODEL_REV to specific commit
3. **Storage bloat** - Run cleanup script weekly
4. **Cache key collisions** - Ensure all params in cache key
5. **Watermarking bypass** - Test free vs paid accounts regularly

## 📞 EMERGENCY CONTACTS

- **Primary:** [DevOps Engineer] - +1-XXX-XXX-XXXX
- **Secondary:** [ML Engineer] - +1-XXX-XXX-XXXX
- **Supabase Support:** https://app.supabase.com/support
- **RunPod Support:** https://www.runpod.io/legal/support

## 📝 POST-INCIDENT REVIEW

After any incident:
1. Create incident report in Notion
2. Update this runbook with lessons learned
3. Schedule blameless postmortem
4. Implement preventive measures

---
**Last Reviewed:** 2025-10-19  
**Next Review Due:** 2025-11-19