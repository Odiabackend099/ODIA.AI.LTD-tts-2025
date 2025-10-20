# 🚨 ON-CALL CHEATSHEET - Dia AI TTS

## Emergency Contacts
- **Primary**: odiadev (GitHub: @odiadev)
- **Secondary**: [Add trusted engineer]
- **Escalation**: [Add senior engineer/CTO]

## 🚨 Emergency Rollback Procedures

### 1. Disable Free Lane (High Load)
```bash
# Stop free lane container
docker stop tts_free

# Re-route all traffic to priority
docker exec -it gateway ./switch_lane priority

# Verify routing
curl -H "X-API-Key: priority_key" http://gateway/whoami
```

### 2. GPU Memory Issues
```bash
# Enable BNB optimization
export DIA_USE_BNB=1
docker restart tts_priority

# Check GPU usage
nvidia-smi
```

### 3. Complete System Failure
```bash
# Rollback to last stable version
git checkout v1.1-clone-enabled
docker compose down
docker compose up -d

# Verify health
curl http://localhost:8000/health
```

## 🔍 Quick Diagnostics

### Check System Health
```bash
# API health
curl http://localhost:8000/health

# Queue status
curl -H "X-API-Key: admin_key" http://localhost:8000/admin/queue-status

# GPU status
nvidia-smi

# Container status
docker ps
```

### Check Logs
```bash
# Priority lane logs
docker logs tts_priority --tail 100

# Free lane logs
docker logs tts_free --tail 100

# Gateway logs
docker logs gateway --tail 100
```

## 📊 Monitoring Alerts

### Critical Alerts (Immediate Action)
- **p95 latency > 6s** (10 min sustained)
- **5xx errors > 1%** (5 min sustained)
- **GPU utilization > 90%** (5 min sustained)
- **Cache hit rate < 25%** (15 min sustained)

### Warning Alerts (Monitor)
- **Queue depth > 50**
- **Memory usage > 80%**
- **Disk usage > 85%**

## 🔧 Common Fixes

### High Latency
1. Check GPU utilization
2. Verify cache hit rate
3. Check queue depth
4. Restart containers if needed

### Memory Issues
1. Enable BNB: `DIA_USE_BNB=1`
2. Restart containers
3. Check for memory leaks

### Authentication Issues
1. Verify API keys in environment
2. Check Supabase connection
3. Restart authentication service

## 🚫 What NOT to Do
- ❌ Don't restart all containers at once
- ❌ Don't change production configs without testing
- ❌ Don't disable monitoring
- ❌ Don't commit secrets to git
- ❌ Don't run untested scripts on production

## 📞 Escalation Path
1. **Level 1**: Check logs, restart containers
2. **Level 2**: Rollback to previous version
3. **Level 3**: Contact senior engineer
4. **Level 4**: Emergency maintenance window

## 🔐 Security Incidents
- **Suspected breach**: Immediately rotate all tokens
- **Secret leak**: Use `git filter-repo` to clean history
- **Unauthorized access**: Disable affected API keys

---
**Last Updated**: $(date)
**Version**: 1.0