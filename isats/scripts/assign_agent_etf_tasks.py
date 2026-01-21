"""
ETF Option Trading Agent Coordinator
Assigns ETF trading tasks to 10 Million Agents
"""
import json
import os

# ETF Universe for Each Agent
AGENT_ETF_ASSIGNMENTS = {
    "01_Scalp": {
        "name": "Scalp Master",
        "etfs": ["122630", "252670"],  # KODEX/TIGER 레버리지
        "strategy": "Short-term scalping on 2x leverage ETFs",
        "market": "BULL",
        "max_position": 10_000_000,
        "rules": "1천만원 이하, 단타 위주"
    },
    "02_Sniper": {
        "name": "Sniper Elite",
        "etfs": ["114800", "123310"],  # KODEX/TIGER 인버스
        "strategy": "Precision PUT trades on market crashes",
        "market": "BEAR",
        "max_position": 5_000,
        "rules": "1천~5천원, 최대 30% 자본"
    },
    "03_Momentum": {
        "name": "Momentum Rider",
        "etfs": ["233740"],  # KODEX 코스닥150레버리지
        "strategy": "Ride KOSDAQ momentum with 2x leverage",
        "market": "BULL",
        "max_position": 10_000_000,
        "rules": "코스닥 강세 시 집중 투자"
    },
    "04_Contrarian": {
        "name": "Contrarian Trader",
        "etfs": ["251340"],  # KODEX 레버리지인버스
        "strategy": "Counter-trend with 2x inverse",
        "market": "BEAR",
        "max_position": 5_000,
        "rules": "급락 시 2배 인버스로 공격"
    },
    "05_Sector": {
        "name": "Sector Specialist",
        "etfs": ["102780", "278530", "371460"],  # 삼성그룹, 2차전지 레버리지
        "strategy": "Sector rotation with leverage",
        "market": "BULL",
        "max_position": 10_000_000,
        "rules": "섹터 강세 포착 후 레버리지"
    },
    "06_Volatility": {
        "name": "Volatility Hunter",
        "etfs": ["252710", "252420"],  # 선물 레버리지/인버스
        "strategy": "Exploit volatility with futures ETFs",
        "market": "NEUTRAL",
        "max_position": 10_000_000,
        "rules": "변동성 확대 시 양방향 거래"
    },
    "07_KOSDAQ_Bear": {
        "name": "KOSDAQ Bear",
        "etfs": ["251350"],  # KODEX 코스닥150인버스
        "strategy": "Short KOSDAQ during weakness",
        "market": "BEAR",
        "max_position": 5_000,
        "rules": "코스닥 약세 시 인버스"
    },
    "08_Balanced": {
        "name": "Balanced Trader",
        "etfs": ["122630", "114800"],  # 레버리지 + 인버스
        "strategy": "Dynamic allocation between CALL/PUT",
        "market": "NEUTRAL",
        "max_position": 10_000_000,
        "rules": "시장 환경 따라 동적 전환"
    },
    "09_Aggressive": {
        "name": "Aggressive Bull",
        "etfs": ["122630", "233740", "102780"],  # 모든 레버리지
        "strategy": "Maximum leverage in bull markets",
        "market": "BULL",
        "max_position": 10_000_000,
        "rules": "강세장 최대 레버리지"
    },
    "10_Defensive": {
        "name": "Defensive Bear",
        "etfs": ["114800", "251340", "251350"],  # 모든 인버스
        "strategy": "Maximum protection in bear markets",
        "market": "BEAR",
        "max_position": 5_000,
        "rules": "약세장 최대 방어"
    }
}

def create_agent_config():
    """Create configuration file for each agent"""
    output_dir = "agent_etf_configs"
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("🤖 ETF 옵션 거래 에이전트 업무 부여")
    print("=" * 80)
    print()
    
    for agent_id, config in AGENT_ETF_ASSIGNMENTS.items():
        # Save config
        config_file = os.path.join(output_dir, f"{agent_id}_config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {agent_id}: {config['name']}")
        print(f"   📊 ETFs: {', '.join(config['etfs'])}")
        print(f"   🎯 Strategy: {config['strategy']}")
        print(f"   🌍 Market: {config['market']}")
        print(f"   💰 Max Position: {config['max_position']:,}원")
        print(f"   📋 Rules: {config['rules']}")
        print()
    
    # Create master assignment file
    master_file = os.path.join(output_dir, "master_assignments.json")
    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(AGENT_ETF_ASSIGNMENTS, f, ensure_ascii=False, indent=2)
    
    print("=" * 80)
    print(f"📁 설정 파일 저장: {output_dir}/")
    print(f"📁 마스터 파일: {master_file}")
    print("=" * 80)
    print()
    
    # Summary
    bull_agents = [a for a, c in AGENT_ETF_ASSIGNMENTS.items() if c['market'] == 'BULL']
    bear_agents = [a for a, c in AGENT_ETF_ASSIGNMENTS.items() if c['market'] == 'BEAR']
    neutral_agents = [a for a, c in AGENT_ETF_ASSIGNMENTS.items() if c['market'] == 'NEUTRAL']
    
    print("📊 에이전트 배치 요약:")
    print(f"   BULL 시장 전담: {len(bull_agents)}명 ({', '.join(bull_agents)})")
    print(f"   BEAR 시장 전담: {len(bear_agents)}명 ({', '.join(bear_agents)})")
    print(f"   중립/변동성: {len(neutral_agents)}명 ({', '.join(neutral_agents)})")
    print()
    print("🚀 모든 에이전트가 ETF 옵션 거래 준비 완료!")

if __name__ == "__main__":
    create_agent_config()
