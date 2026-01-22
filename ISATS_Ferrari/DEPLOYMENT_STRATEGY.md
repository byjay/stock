# 🎯 ISATS v6.0 - 최종 배포 전략

**작성 일시:** 2026-01-22 10:41:00  
**전략:** 로컬 Docker 우선 → 수익 발생 후 클라우드 전환

---

## 💡 배포 전략 (단계별)

### Phase 1: 로컬 Docker 운영 (현재 단계) ✅

**목표:** 무료로 시스템 검증 + 수익 창출

**장점:**
- ✅ **완전 무료** (전기세만 발생)
- ✅ **완전한 제어** (모든 설정 자유)
- ✅ **빠른 개발** (즉시 수정 가능)
- ✅ **데이터 보안** (로컬 저장)

**실행 방법:**
```bash
# 1. Docker Compose로 전체 시스템 실행
cd c:\Users\FREE\Desktop\주식\ISATS_Ferrari
docker-compose up -d

# 2. 상태 확인
docker-compose ps

# 3. 로그 확인
docker-compose logs -f

# 4. 대시보드 접속
http://localhost
```

**비용:** $0 (무료)

---

### Phase 2: 수익 검증 (목표: 월 100만원 이상)

**검증 기간:** 최소 3개월

**체크리스트:**
- [ ] 월 수익률 5% 이상 달성
- [ ] 3개월 연속 수익 달성
- [ ] 최대 손실 -10% 이내 유지
- [ ] 시스템 안정성 99% 이상

**기록 사항:**
- 일일 수익/손실 기록
- 매매 내역 저장
- 시스템 가동 시간 기록
- 에러 발생 빈도 기록

---

### Phase 3: 클라우드 전환 (수익 발생 후)

**전환 조건:**
- ✅ 월 수익 100만원 이상 달성
- ✅ 3개월 연속 안정적 수익
- ✅ 시스템 안정성 검증 완료

**권장 플랫폼:** Google Cloud Run

**이유:**
- ✅ 자동 스케일링 (트래픽 증가 시 자동 확장)
- ✅ 무료 티어 제공 (초기 비용 절감)
- ✅ 한국 리전 지원 (낮은 지연시간)
- ✅ Docker 직접 배포 (기존 설정 그대로 사용)

**예상 비용:**
- 무료 티어: 월 200만 요청 무료
- 초과 시: 월 $10~30 예상

---

## 🐳 로컬 Docker 운영 가이드

### 1️⃣ 시스템 시작

```bash
# 전체 시스템 시작
docker-compose up -d

# 개별 서비스 시작
docker-compose up -d redis        # Redis만
docker-compose up -d api_server   # API 서버만
docker-compose up -d main_engine  # 메인 엔진만
```

### 2️⃣ 시스템 중지

```bash
# 전체 중지
docker-compose down

# 데이터 보존하며 중지
docker-compose stop

# 특정 서비스만 중지
docker-compose stop main_engine
```

### 3️⃣ 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f api_server
docker-compose logs -f main_engine

# 최근 100줄만
docker-compose logs --tail=100
```

### 4️⃣ 시스템 업데이트

```bash
# 1. 코드 수정 후
# 2. 컨테이너 재빌드
docker-compose build

# 3. 재시작
docker-compose up -d
```

### 5️⃣ 데이터 백업

```bash
# 1. 중요 파일 백업
cp ISATS_Ferrari/daily_target_list.csv backup/
cp ISATS_Ferrari/config/secrets.yaml backup/
cp -r ISATS_Ferrari/brain backup/

# 2. Docker 볼륨 백업
docker run --rm -v isats_ferrari_redis_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar czf /backup/redis_data.tar.gz /data
```

---

## 💰 비용 비교

### 로컬 Docker (현재)

| 항목 | 비용 |
|------|------|
| 서버 | $0 (PC 사용) |
| 전기세 | 월 ~$5 (24시간 가동 시) |
| 인터넷 | $0 (기존 회선 사용) |
| **총 비용** | **월 ~$5** |

### Google Cloud Run (수익 후)

| 항목 | 비용 |
|------|------|
| 컴퓨팅 | 무료 티어 or 월 $10~20 |
| Redis (Memorystore) | 월 $30~50 |
| 네트워크 | 월 $5~10 |
| **총 비용** | **월 $45~80** |

**결론:** 로컬 Docker가 **월 $40~75 절약!**

---

## 🔄 클라우드 전환 시나리오 (미래)

### 전환 시점 판단

**수익 기준:**
```
월 수익 > 클라우드 비용 x 10

예시:
- 클라우드 비용: 월 $50
- 필요 수익: 월 $500 (약 60만원)
```

**안정성 기준:**
- 3개월 연속 수익
- 최대 손실 -10% 이내
- 시스템 가동률 99% 이상

### 전환 절차

```bash
# 1. Google Cloud SDK 설치
# https://cloud.google.com/sdk/docs/install

# 2. 프로젝트 생성
gcloud projects create isats-ferrari-prod

# 3. 컨테이너 빌드
gcloud builds submit --tag gcr.io/isats-ferrari-prod/api-server

# 4. Cloud Run 배포
gcloud run deploy isats-api \
  --image gcr.io/isats-ferrari-prod/api-server \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars KIS_APP_KEY=$KIS_APP_KEY,KIS_SECRET_KEY=$KIS_SECRET_KEY

# 5. Redis 설정 (Memorystore)
gcloud redis instances create isats-redis \
  --size=1 \
  --region=asia-northeast3 \
  --redis-version=redis_7_0

# 6. 도메인 연결 (선택)
gcloud run domain-mappings create \
  --service isats-api \
  --domain isats.yourdomain.com
```

---

## 📊 성과 추적 (로컬 운영 중)

### 일일 체크리스트

```bash
# 1. 시스템 상태 확인
docker-compose ps

# 2. 로그 확인
docker-compose logs --tail=100

# 3. 대시보드 확인
http://localhost

# 4. 수익/손실 기록
# → Excel 또는 Google Sheets에 기록
```

### 주간 체크리스트

```bash
# 1. 백업
./backup.sh

# 2. 시스템 업데이트
git pull
docker-compose build
docker-compose up -d

# 3. 성과 분석
# → 주간 수익률 계산
# → 전략 효과성 분석
```

### 월간 체크리스트

```bash
# 1. 월간 수익 정산
# 2. 클라우드 전환 여부 검토
# 3. 시스템 최적화
```

---

## 🎯 목표 로드맵

### Q1 2026 (현재)
- ✅ 로컬 Docker 시스템 구축 완료
- 🔄 3개월 수익 검증 진행 중
- 목표: 월 수익 50만원 달성

### Q2 2026
- 목표: 월 수익 100만원 달성
- 시스템 안정성 99% 달성
- 클라우드 전환 검토 시작

### Q3 2026
- 클라우드 전환 (조건 충족 시)
- 자동화 고도화
- 다중 계좌 운영 검토

### Q4 2026
- 수익 극대화
- 시스템 확장
- 추가 전략 개발

---

## ⚠️ 주의사항

### 로컬 Docker 운영 시

1. **전원 관리**
   - PC 절전 모드 비활성화
   - UPS(무정전 전원 장치) 권장

2. **네트워크 안정성**
   - 안정적인 인터넷 연결 필수
   - 백업 인터넷 회선 권장

3. **데이터 백업**
   - 일일 백업 자동화
   - 외부 저장소 백업 (Google Drive, Dropbox)

4. **보안**
   - 방화벽 설정
   - 외부 접속 차단
   - API 키 안전 보관

---

## 📞 문제 해결

### Docker 컨테이너가 중지됨

```bash
# 1. 로그 확인
docker-compose logs

# 2. 재시작
docker-compose restart

# 3. 완전 재시작
docker-compose down
docker-compose up -d
```

### 메모리 부족

```bash
# 1. Docker 메모리 제한 증가
# docker-compose.yml 수정:
# deploy:
#   resources:
#     limits:
#       memory: 4G

# 2. 재시작
docker-compose up -d
```

### 디스크 공간 부족

```bash
# 1. Docker 정리
docker system prune -a

# 2. 로그 정리
docker-compose logs --tail=0 > /dev/null
```

---

## 🚀 최종 권장 사항

### 현재 단계 (Phase 1)

**✅ 로컬 Docker로 시작하세요!**

**이유:**
1. **무료** - 비용 부담 없음
2. **안전** - 실전 전 충분한 검증
3. **유연** - 즉시 수정 가능
4. **학습** - 시스템 이해도 향상

### 미래 단계 (Phase 3)

**수익 발생 후 클라우드 전환**

**조건:**
- 월 수익 100만원 이상
- 3개월 연속 안정적 수익
- 시스템 안정성 검증 완료

**플랫폼:** Google Cloud Run

---

**작성자:** ISATS Neural Swarm  
**버전:** 6.0 (Deployment Strategy)  
**최종 업데이트:** 2026-01-22 10:41:00  
**전략:** 로컬 우선 → 수익 후 클라우드 ✅
