# 🌐 ISATS v6.0 - 배포 플랫폼 가이드

**작성 일시:** 2026-01-22 10:33:00  
**중요:** 이 시스템은 **백엔드 서버가 필요**합니다!

---

## ⚠️ 중요: Netlify는 사용 불가!

### ❌ Netlify가 안 되는 이유

**Netlify는 정적 사이트 호스팅만 지원합니다.**

ISATS v6.0은 다음 백엔드 기능이 필수입니다:
- ✅ Python 실행 환경
- ✅ Redis 서버
- ✅ WebSocket 서버 (FastAPI)
- ✅ 실시간 데이터 처리
- ✅ 백그라운드 작업 (Watchers)

**Netlify는 HTML/CSS/JS만 서빙 가능** → 백엔드 불가 ❌

---

## ✅ 권장 배포 플랫폼

### 1️⃣ **Google Cloud Run** (추천 ⭐⭐⭐⭐⭐)

**장점:**
- ✅ Docker 컨테이너 직접 배포
- ✅ 자동 스케일링
- ✅ 무료 티어 제공
- ✅ Redis 연동 가능 (Cloud Memorystore)
- ✅ 한국 리전 지원 (asia-northeast3)

**배포 방법:**
```bash
# 1. Google Cloud SDK 설치
gcloud init

# 2. 프로젝트 생성
gcloud projects create isats-ferrari

# 3. 컨테이너 빌드
gcloud builds submit --tag gcr.io/isats-ferrari/api-server

# 4. Cloud Run 배포
gcloud run deploy isats-api \
  --image gcr.io/isats-ferrari/api-server \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

**비용:**
- 무료 티어: 월 200만 요청, 360,000 GB-초
- 초과 시: $0.40/100만 요청

---

### 2️⃣ **AWS EC2** (안정적 ⭐⭐⭐⭐)

**장점:**
- ✅ 완전한 서버 제어
- ✅ Redis 직접 설치 가능
- ✅ 고성능
- ✅ 한국 리전 (ap-northeast-2)

**배포 방법:**
```bash
# 1. EC2 인스턴스 생성 (Ubuntu 22.04)
# 2. SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Docker 설치
sudo apt update
sudo apt install docker.io docker-compose -y

# 4. 프로젝트 클론
git clone https://github.com/your-repo/ISATS_Ferrari.git
cd ISATS_Ferrari

# 5. Docker Compose 실행
sudo docker-compose up -d
```

**비용:**
- t2.micro (무료 티어): 월 750시간 무료
- t3.small (권장): 월 $15~20

---

### 3️⃣ **Heroku** (간편 ⭐⭐⭐)

**장점:**
- ✅ Git push만으로 배포
- ✅ Redis 애드온 제공
- ✅ 간편한 관리

**배포 방법:**
```bash
# 1. Heroku CLI 설치
# 2. 로그인
heroku login

# 3. 앱 생성
heroku create isats-ferrari

# 4. Redis 애드온 추가
heroku addons:create heroku-redis:hobby-dev

# 5. 배포
git push heroku main
```

**비용:**
- Hobby: 월 $7
- Redis: 월 $3~15

---

### 4️⃣ **Digital Ocean** (가성비 ⭐⭐⭐⭐)

**장점:**
- ✅ 저렴한 가격
- ✅ Docker 지원
- ✅ 간단한 설정

**배포 방법:**
```bash
# 1. Droplet 생성 (Docker 이미지 선택)
# 2. SSH 접속
ssh root@your-droplet-ip

# 3. 프로젝트 클론 및 실행
git clone https://github.com/your-repo/ISATS_Ferrari.git
cd ISATS_Ferrari
docker-compose up -d
```

**비용:**
- Basic Droplet: 월 $6~12

---

### 5️⃣ **로컬 서버** (개발/테스트용 ⭐⭐⭐⭐⭐)

**장점:**
- ✅ 완전 무료
- ✅ 완전한 제어
- ✅ 빠른 개발

**실행 방법:**
```bash
# Docker Compose 사용
cd ISATS_Ferrari
docker-compose up -d

# 또는 직접 실행
python api_server.py  # 터미널 1
python main.py        # 터미널 2
```

**접속:**
- 대시보드: http://localhost
- API: http://localhost:8000

---

## 🔐 보안 설정 (중요!)

### 1. secrets.yaml 보호

**절대 Git에 커밋하지 마세요!**

`.gitignore`에 이미 추가되어 있습니다:
```
config/secrets.yaml
```

### 2. 환경 변수 사용 (권장)

**배포 시 환경 변수로 API 키 주입:**

```bash
# Google Cloud Run
gcloud run deploy isats-api \
  --set-env-vars KIS_APP_KEY=your_key,KIS_SECRET_KEY=your_secret

# Heroku
heroku config:set KIS_APP_KEY=your_key
heroku config:set KIS_SECRET_KEY=your_secret

# Docker
docker run -e KIS_APP_KEY=your_key -e KIS_SECRET_KEY=your_secret ...
```

### 3. secrets.yaml 템플릿

**Git에는 템플릿만 커밋:**

```yaml
# config/secrets.yaml.template
key:
  kis_app_key: "YOUR_APP_KEY_HERE"
  kis_secret_key: "YOUR_SECRET_KEY_HERE"
  account_no: "YOUR_ACCOUNT_NO"
system:
  mode: "VIRTUAL"
```

**실제 사용 시:**
```bash
cp config/secrets.yaml.template config/secrets.yaml
# 실제 키 입력
```

---

## 📊 플랫폼 비교표

| 플랫폼 | 난이도 | 비용 | 성능 | 추천도 |
|--------|--------|------|------|--------|
| **Google Cloud Run** | 중 | 무료~저렴 | 높음 | ⭐⭐⭐⭐⭐ |
| **AWS EC2** | 중~상 | 중간 | 매우 높음 | ⭐⭐⭐⭐ |
| **Heroku** | 하 | 저렴 | 중간 | ⭐⭐⭐ |
| **Digital Ocean** | 중 | 저렴 | 높음 | ⭐⭐⭐⭐ |
| **로컬 서버** | 하 | 무료 | 높음 | ⭐⭐⭐⭐⭐ (개발용) |
| **Netlify** | - | - | - | ❌ 불가 |

---

## 🚀 권장 배포 순서

### Phase 1: 로컬 테스트
```bash
# 1. 로컬에서 Docker Compose 실행
docker-compose up -d

# 2. 시스템 검증
python ISATS_Ferrari/tests/verify_full_system.py

# 3. 대시보드 접속 확인
http://localhost
```

### Phase 2: 클라우드 배포
```bash
# 1. Google Cloud Run 배포 (추천)
gcloud run deploy isats-api --source .

# 2. 환경 변수 설정
gcloud run services update isats-api \
  --set-env-vars KIS_APP_KEY=xxx,KIS_SECRET_KEY=xxx

# 3. 접속 확인
https://isats-api-xxx.run.app
```

### Phase 3: 도메인 연결 (선택)
```bash
# 1. 도메인 구매 (예: isats.com)
# 2. Cloud Run에 도메인 매핑
gcloud run domain-mappings create \
  --service isats-api \
  --domain isats.com
```

---

## ❓ FAQ

### Q1: Netlify에 꼭 배포하고 싶은데요?
**A:** Netlify는 **대시보드(HTML)만** 호스팅 가능합니다.  
백엔드(Python, Redis)는 별도 서버 필요합니다.

**해결책:**
- 대시보드: Netlify
- 백엔드: Google Cloud Run

### Q2: 무료로 배포 가능한가요?
**A:** 네! Google Cloud Run 무료 티어로 충분합니다.

### Q3: API 키가 노출되지 않을까요?
**A:** `.gitignore`에 `config/secrets.yaml`이 추가되어 있어 안전합니다.  
환경 변수 사용을 권장합니다.

---

**작성자:** ISATS Neural Swarm  
**버전:** 6.0 (Deployment Guide)  
**최종 업데이트:** 2026-01-22 10:33:00
