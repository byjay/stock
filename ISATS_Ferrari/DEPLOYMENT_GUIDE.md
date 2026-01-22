# 🚀 ISATS v6.0 "FERRARI" - 배포 가이드

**작성 일시:** 2026-01-22 10:13:00  
**작전명:** OPERATION LAUNCH (출격)  
**상태:** READY TO DEPLOY

---

## 📋 사전 준비

### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

**예상 출력:**
```
Docker version 24.0.0
Docker Compose version v2.20.0
```

### 2. 필수 파일 확인
```
ISATS_Ferrari/
├── Dockerfile ✅
├── docker-compose.yml ✅
├── requirements.txt ✅
├── nginx.conf ✅
├── api_server.py ✅
├── main.py ✅
└── dashboard/
    └── mts_supreme_v3.html ✅
```

---

## 🐳 Docker 빌드 및 실행

### Step 1: 이미지 빌드
```bash
cd c:\Users\FREE\Desktop\주식\ISATS_Ferrari
docker-compose build
```

**예상 소요 시간:** 3~5분

**예상 출력:**
```
[+] Building 180.5s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.2kB
 => [internal] load .dockerignore
 => [1/8] FROM docker.io/library/python:3.11-slim
 => [2/8] RUN apt-get update && apt-get install -y gcc g++ git curl redis-server
 => [3/8] COPY requirements.txt .
 => [4/8] RUN pip install --no-cache-dir --upgrade pip
 => [5/8] RUN pip install --no-cache-dir -r requirements.txt
 => [6/8] COPY . .
 => [7/8] RUN mkdir -p /app/data/KR /app/data/US /app/logs /app/brain /app/config
 => exporting to image
 => => naming to docker.io/library/isats_ferrari_api_server
```

### Step 2: 컨테이너 실행
```bash
docker-compose up -d
```

**예상 출력:**
```
[+] Running 5/5
 ✔ Network isats_ferrari_isats_network  Created
 ✔ Volume "isats_ferrari_redis_data"    Created
 ✔ Container isats_redis                Started
 ✔ Container isats_api_server           Started
 ✔ Container isats_main_engine          Started
 ✔ Container isats_dashboard            Started
```

### Step 3: 상태 확인
```bash
docker-compose ps
```

**예상 출력:**
```
NAME                 IMAGE                      STATUS         PORTS
isats_redis          redis:7-alpine             Up 10 seconds  0.0.0.0:6379->6379/tcp
isats_api_server     isats_ferrari_api_server   Up 8 seconds   0.0.0.0:8000->8000/tcp
isats_main_engine    isats_ferrari_main_engine  Up 6 seconds
isats_dashboard      nginx:alpine               Up 4 seconds   0.0.0.0:80->80/tcp
```

### Step 4: 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f api_server
docker-compose logs -f main_engine
```

---

## 🌐 접속 확인

### 1. API 서버
```
http://localhost:8000
http://localhost:8000/docs (Swagger UI)
```

### 2. 대시보드
```
http://localhost
http://localhost/mts_supreme_v3.html
```

### 3. WebSocket
```
ws://localhost:8000/ws
```

---

## 🔧 에러 대응 체계

### ⚠️ 에러 발생 시 자동 진단

**audit_codebase.py (진단기) 실행:**
```bash
python audit_codebase.py
```

**예상 출력:**
```
================================================================================
🔍 ISATS v6.0 Code Audit Report
================================================================================
📂 Scanning: c:\Users\FREE\Desktop\주식\ISATS_Ferrari
📊 Total Files: 180

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐛 Issues Found
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ERROR] main.py:45 - ImportError: No module named 'redis'
[WARNING] api_server.py:120 - Unused variable 'result'
[INFO] watchers.py:200 - TODO: Implement KIS API integration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Issues: 3
- Errors: 1
- Warnings: 1
- Info: 1
```

### 🔨 자동 수리 프로세스

1. **진단기 실행**
   ```bash
   python audit_codebase.py > audit_report.txt
   ```

2. **로그 분석**
   - 에러 타입 확인
   - 파일 위치 확인
   - 원인 파악

3. **자동 수리 (AI)**
   - 로그를 AI에게 전달
   - 자동 코드 수정
   - 재배포

---

## 🛠️ 유용한 Docker 명령어

### 컨테이너 관리
```bash
# 전체 시작
docker-compose up -d

# 전체 중지
docker-compose down

# 재시작
docker-compose restart

# 특정 서비스 재시작
docker-compose restart api_server
```

### 로그 관리
```bash
# 실시간 로그
docker-compose logs -f

# 최근 100줄
docker-compose logs --tail=100

# 특정 서비스 로그
docker-compose logs -f main_engine
```

### 컨테이너 접속
```bash
# API 서버 접속
docker exec -it isats_api_server bash

# Main Engine 접속
docker exec -it isats_main_engine bash

# Redis 접속
docker exec -it isats_redis redis-cli
```

### 리소스 확인
```bash
# 컨테이너 리소스 사용량
docker stats

# 디스크 사용량
docker system df
```

---

## 🔥 실전 배포 체크리스트

### ✅ 배포 전 확인

- [ ] **데이터 준비**
  - [ ] `data/KR/` 폴더에 500+ CSV 파일
  - [ ] `data/US/` 폴더에 497+ CSV 파일
  - [ ] `daily_target_list.csv` 생성 완료

- [ ] **설정 파일**
  - [ ] `config/secrets.yaml` 작성 (KIS API 키)
  - [ ] `MODE: "VIRTUAL"` 설정 확인

- [ ] **Docker 이미지**
  - [ ] `docker-compose build` 성공
  - [ ] 이미지 크기 확인 (약 1~2GB)

- [ ] **네트워크**
  - [ ] 포트 8000 사용 가능 확인
  - [ ] 포트 80 사용 가능 확인
  - [ ] 포트 6379 사용 가능 확인

### ✅ 배포 후 확인

- [ ] **서비스 상태**
  - [ ] `docker-compose ps` 모두 Up 상태
  - [ ] Health Check 통과

- [ ] **API 서버**
  - [ ] http://localhost:8000 접속 성공
  - [ ] http://localhost:8000/docs Swagger UI 확인

- [ ] **대시보드**
  - [ ] http://localhost 접속 성공
  - [ ] WebSocket 연결 성공 (녹색 표시)
  - [ ] 실시간 로그 스트림 확인

- [ ] **Main Engine**
  - [ ] `docker-compose logs main_engine` 로그 확인
  - [ ] Sniper/Scout/Patrol 배치 확인
  - [ ] Redis 연결 성공 확인

### ✅ 실전 전환 (주의!)

- [ ] **모의투자 검증**
  - [ ] 최소 1주일 모의투자 운영
  - [ ] 수익률 검증
  - [ ] 에러 없음 확인

- [ ] **리스크 관리**
  - [ ] 포지션 사이징 로직 검증
  - [ ] 손절 로직 검증
  - [ ] 최대 손실 제한 설정

- [ ] **실전 전환**
  - [ ] `config/secrets.yaml` MODE를 "REAL"로 변경
  - [ ] `strategy/active_bot.py` IS_REAL_TRADING = True
  - [ ] 재배포: `docker-compose restart`

---

## 🚨 긴급 중지

### 즉시 중지
```bash
docker-compose down
```

### 데이터 보존하며 중지
```bash
docker-compose stop
```

### 완전 삭제 (주의!)
```bash
docker-compose down -v
```

---

## 📞 문제 해결

### 1. 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose logs

# 특정 서비스 로그
docker-compose logs api_server
```

### 2. 포트 충돌
```bash
# 포트 사용 확인 (Windows)
netstat -ano | findstr :8000
netstat -ano | findstr :80
netstat -ano | findstr :6379

# 프로세스 종료
taskkill /PID [PID번호] /F
```

### 3. Redis 연결 실패
```bash
# Redis 상태 확인
docker exec -it isats_redis redis-cli ping

# 응답: PONG (정상)
```

### 4. 메모리 부족
```bash
# Docker 메모리 제한 증가
# docker-compose.yml에 추가:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

---

## 🎯 성능 최적화

### 1. Redis 최적화
```bash
# redis.conf 설정
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 2. Python 최적화
```bash
# 환경 변수 설정
PYTHONOPTIMIZE=1
PYTHONDONTWRITEBYTECODE=1
```

### 3. Nginx 최적화
```nginx
# nginx.conf에 추가
worker_processes auto;
worker_connections 2048;
```

---

**작성자:** ISATS Neural Swarm  
**버전:** 6.0 (Docker Deployment)  
**최종 업데이트:** 2026-01-22 10:13:00  
**상태:** READY TO LAUNCH 🚀
