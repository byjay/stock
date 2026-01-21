import aiohttp
import asyncio
import yaml
import json
import os
from datetime import datetime

# ==========================================
# 🎯 KIS API 상한가 종목 스캐너
# ==========================================

async def get_upper_limit_stocks():
    """오늘의 상한가 종목 가져오기"""
    
    # 1. 설정 로드
    config_path = "ISATS_Ferrari/config/secrets.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    app_key = config['key']['kis_app_key']
    app_secret = config['key']['kis_secret_key']
    base_url = "https://openapi.koreainvestment.com:9443"
    
    print("="*60)
    print(f"      🎯 오늘의 상한가 종목 스캔 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*60)
    
    # 2. Access Token 발급
    print("\n📡 [Step 1] Access Token 발급 중...")
    auth_url = f"{base_url}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # 토큰 발급
        async with session.post(auth_url, json=payload) as resp:
            token_data = await resp.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                print(f"❌ 토큰 발급 실패: {token_data}")
                return
            
            print(f"✅ Access Token 발급 완료")
        
        # 3. 상한가 종목 조회 (등락률 상위 종목 API 활용)
        print("\n📊 [Step 2] 상한가 종목 조회 중...")
        
        # KIS API: 국내주식 등락률 순위 조회
        rank_url = f"{base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {access_token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": "FHPST01710000"  # 등락률 순위 조회 TR
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식
            "FID_COND_SCR_DIV_CODE": "20171",  # 등락률 상위
            "FID_INPUT_ISCD": "0000",  # 전체
            "FID_DIV_CLS_CODE": "0",  # 전체
            "FID_BLNG_CLS_CODE": "0",  # 평균거래량
            "FID_TRGT_CLS_CODE": "111111111",  # 전체
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": ""
        }
        
        async with session.get(rank_url, headers=headers, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"❌ API 호출 실패 (Status: {resp.status})")
                print(f"   응답: {text}")
                return
            
            data = await resp.json()
            
            # 4. 결과 파싱
            if data.get('rt_cd') != '0':
                print(f"❌ 조회 실패: {data.get('msg1')}")
                return
            
            stocks = data.get('output', [])
            
            if not stocks:
                print("⚠️ 상한가 종목이 없거나 데이터를 가져올 수 없습니다.")
                return
            
            # 5. 상한가 종목 필터링 (등락률 +29% 이상)
            upper_limit_stocks = []
            for stock in stocks:
                try:
                    change_rate = float(stock.get('prdy_ctrt', '0'))  # 전일대비율
                    if change_rate >= 29.0:  # 상한가 기준
                        upper_limit_stocks.append({
                            'code': stock.get('mksc_shrn_iscd'),
                            'name': stock.get('hts_kor_isnm'),
                            'price': stock.get('stck_prpr'),
                            'change_rate': change_rate,
                            'volume': stock.get('acml_vol')
                        })
                except:
                    continue
            
            # 6. 결과 출력
            print(f"\n🎉 [Result] 상한가 종목 {len(upper_limit_stocks)}개 발견!")
            print("="*60)
            
            if upper_limit_stocks:
                for i, stock in enumerate(upper_limit_stocks[:10], 1):  # 상위 10개만
                    print(f"{i:2d}. [{stock['code']}] {stock['name']}")
                    print(f"    가격: {stock['price']:>10}원 | 등락률: +{stock['change_rate']:.2f}% | 거래량: {stock['volume']}")
                    print()
            else:
                print("⚠️ 오늘은 상한가 종목이 없습니다.")
            
            print("="*60)
            
            # 7. CSV 저장
            if upper_limit_stocks:
                import pandas as pd
                df = pd.DataFrame(upper_limit_stocks)
                save_path = f"ISATS_Ferrari/data/upper_limit_{datetime.now().strftime('%Y%m%d')}.csv"
                df.to_csv(save_path, index=False, encoding='utf-8-sig')
                print(f"💾 저장 완료: {save_path}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(get_upper_limit_stocks())
