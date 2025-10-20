# ODIADEV-TTS On-Call Cheatsheet

**Version:** v1.2-prod-ready  
**Last Updated:** 2025-10-19  
**Author:** CROSSO Engineering Team

## 🚨 EMERGENCY RESPONSE

### 🔥 OOM (Out of Memory)
**Symptoms:** 500 errors, GPU 100% for >10s, nvidia-smi >15.5GB

```bash
# 1. Kill free lane first
pkill -f "uvicorn.*8001"

# 2. Check if priority lane recovers
curl -s http://localhost:8000/health

# 3. If still OOM, disable voice cloning
export DISABLE_VOICE_CLONING=1

# 4. Flip to 8-bit quantization
export DIA_USE_BNB=1
# Restart both lanes

# 5. If still failing, scale to A10G via RunPod dashboard
```

### 🐌 Latency Spike
**Symptoms:** p95 > 6s for 10+ min, queue > 10

```bash
# 1. Throttle free lane
# Edit infra/env.free and reduce MAX_CONCURRENT to 1

# 2. Return 429s faster
# Edit middleware/security.py and reduce rate limits

# 3. Check GPU utilization
watch -n 2 nvidia-smi

# 4. If persists > 15min, scale to A10G
```

### 🗑️ Storage Surge
**Symptoms:** Disk usage spiking, clone failures

```bash
# 1. Pause clone endpoint
export DISABLE_VOICE_CLONING=1

# 2. Run cleanup for temp uploads >24h
python scripts/lifecycle_policy.py

# 3. Check storage usage
df -h

# 4. Notify team
```

### 💧 Watermark Bug
**Symptoms:** Reports of missing watermarks for free users

```bash
# 1. Disable TTS for free lane
# Temporarily stop free lane service

# 2. Hotfix server-side check
# Edit backend/app/middleware/security.py
# Force watermark for LANE=free

# 3. Re-enable after fix
```

## 📊 HEALTH CHECKS

### 🔍 Lane Status
```bash
# Priority Lane
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/metrics | jq

# Free Lane
curl -s http://localhost:8001/health | jq
curl -s http://localhost:8001/metrics | jq

# Check lane identification
curl -s http://localhost:8000/whoami | jq  # Should return {"lane": "priority"}
curl -s http://localhost:8001/whoami | jq  # Should return {"lane": "free"}
```

### 📈 Key Metrics
```bash
# Cache hit rate (target ≥ 40%)
curl -s http://localhost:8000/metrics | jq '.cache_hit_rate'

# Latency (p50 ≤ 3.5s, p95 < 6s)
curl -s http://localhost:8000/metrics | jq '.average_latency'

# Error rate (target < 1%)
curl -s http://localhost:8000/metrics | jq '.error_count'

# GPU utilization (target < 90%)
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits
```

### 🔧 Service Status
```bash
# Check if services are running
ps aux | grep uvicorn

# Check Redis
redis-cli ping  # Should return PONG

# Check disk space
df -h /

# Check memory
free -h
```

## 🔧 OPERATIONAL COMMANDS

### 🔄 Restart Services
```bash
# Restart Priority Lane
pkill -f "uvicorn.*8000"
cd /workspace/backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file /workspace/infra/env.priority &

# Restart Free Lane
pkill -f "uvicorn.*8001"
cd /workspace/backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --env-file /workspace/infra/env.free &

# Check logs
tail -f /var/log/odia-tts-priority.log
tail -f /var/log/odia-tts-free.log
```

### 🧹 Maintenance
```bash
# Force cache clear
redis-cli -h localhost -p 6379 flushall

# Run cleanup script
python scripts/lifecycle_policy.py

# Check for abandoned files
find /tmp -name "*.wav" -mtime +1 -delete
```

### 📊 Monitoring
```bash
# Watch GPU
watch -n 2 nvidia-smi

# Watch system resources
htop

# Watch logs
tail -f /var/log/odia-tts-*.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

## 🚨 ALERT THRESHOLDS

| Metric | Threshold | Action |
|--------|-----------|--------|
| **p95 latency** | > 6s for 10min | Throttle free lane, consider scaling |
| **5xx errors** | > 1% for 5min | Investigate service health |
| **GPU utilization** | > 90% for 5min | Scale to A10G or reduce load |
| **Cache hit rate** | < 25% for 60min | Check cache key integrity |
| **Queue depth** | > 10 for 5min | Return 429s, reduce concurrency |

## 📞 CONTACT LIST

### 🚨 Primary Response
- **DevOps Engineer**: [Name] - +1-XXX-XXX-XXXX
- **ML Engineer**: [Name] - +1-XXX-XXX-XXXX

### 🔧 Support Channels
- **Supabase**: https://app.supabase.com/support
- **RunPod**: https://www.runpod.io/legal/support
- **HuggingFace**: https://huggingface.co/support

### 📧 Notification Emails
- **Critical Alerts**: team@odia.dev
- **Performance Issues**: ops@odia.dev
- **Security Events**: security@odia.dev

## 🔁 ROLLBACK PROCEDURES

### 🔄 Full Rollback
```bash
# 1. Tag current state
git tag rollback-$(date +%s) && git push origin rollback-$(date +%s)

# 2. Switch to previous image
# In RunPod: Change image to v1.1-clone-enabled

# 3. Verify rollback
curl -s http://localhost:8000/health | jq
```

### 🚫 Emergency Rollback
```bash
# 1. Disable voice cloning entirely
export DISABLE_VOICE_CLONING=1

# 2. Switch to v1.0 image
# In RunPod: Change image to v1.0-aida-stable

# 3. Purge queue and restart
```

## 📋 DAILY CHECKLIST

### ☀️ Morning Check (9:00 AM)
- [ ] Check lane health (`/health` endpoints)
- [ ] Review error logs from last 24h
- [ ] Verify GPU utilization < 80%
- [ ] Check cache hit rate > 35%
- [ ] Confirm storage usage < 80%

### 🌙 Evening Check (6:00 PM)
- [ ] Run cleanup script
- [ ] Review performance metrics
- [ ] Check for pending alerts
- [ ] Prepare incident report if needed
- [ ] Update this cheatsheet with lessons learned

## 🛠️ TROUBLESHOOTING

### ❓ Common Issues

**Q: TTS requests timing out**
A: Check GPU utilization, model loading logs, and Redis connectivity

**Q: Cache misses are too high**
A: Verify cache keys include all parameters, check Redis connectivity

**Q: Watermark not appearing**
A: Check LANE environment variable, verify plan detection logic

**Q: Rate limiting not working**
A: Check in-memory rate limit storage, verify API key extraction

### 🔍 Debug Commands

```bash
# Check environment variables
printenv | grep -E "(LANE|PORT|REDIS)"

# Check model loading
grep "DIA model loaded" /var/log/odia-tts-*.log

# Check Redis connection
redis-cli -h localhost -p 6379 ping

# Check API key validation
curl -s -H "X-API-Key: invalid-key" http://localhost:8000/health
```

---
**Last Reviewed:** 2025-10-19  
**Next Review Due:** 2025-11-19