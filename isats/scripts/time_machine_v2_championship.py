import pandas as pd
import numpy as np
import os
import glob
import json

# --- FRICTION CONSTANTS ---
LATENCY = 1
SLIPPAGE = 0.002
IMPACT_FACT = 0.01
TAX = 0.22
INITIAL_CAPITAL = 10_000_000 # KRW 10M as requested

# --- AGENT DEFINITIONS (Personas) ---
AGENTS = [
    {"id": "Hyper_Sniper", "rsi": 10, "tp": 2.5, "sl": 1.5, "size": 0.8},
    {"id": "Aggressive_Trend", "rsi": 30, "tp": 50.0, "sl": 10.0, "size": 0.5},
    {"id": "Safety_Swinger", "rsi": 20, "tp": 5.0, "sl": 3.0, "size": 0.3},
    {"id": "Moonshot_Seeker", "rsi": 35, "tp": 100.0, "sl": 15.0, "size": 0.7},
    {"id": "Tight_Range", "rsi": 25, "tp": 1.0, "sl": 0.5, "size": 0.9},
    {"id": "Middle_Way", "rsi": 22, "tp": 10.0, "sl": 5.0, "size": 0.4},
    {"id": "Risk_Averse", "rsi": 15, "tp": 3.0, "sl": 5.0, "size": 0.1},
    {"id": "Heavy_Weight", "rsi": 30, "tp": 5.0, "sl": 2.0, "size": 0.9},
    {"id": "Volatility_Bet", "rsi": 28, "tp": 25.0, "sl": 10.0, "size": 0.6},
    {"id": "Bot_Zero", "rsi": 30, "tp": 3.0, "sl": 3.0, "size": 0.5}
]

def calculate_causal_indicators(df):
    close = df['close'].squeeze()
    # RSI
    delta = close.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0; down[down > 0] = 0
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.abs().ewm(alpha=1/14, adjust=False).mean()
    df['rsi'] = 100.0 - (100.0 / (1.0 + roll_up / (roll_down + 1e-9)))
    
    # BB
    df['bb_mid'] = close.rolling(20).mean()
    df['bb_low'] = df['bb_mid'] - 1.2 * close.rolling(20).std()
    return df

def simulate_agent_multi_tf(dataset, agent):
    """
    Mainly uses 1h for signals but can be extended to D/W.
    For this experiment, we use the high-precision 1h data resampled from ticks.
    """
    df = dataset['1h']
    df = calculate_causal_indicators(df)
    
    equity = INITIAL_CAPITAL
    position = 0 # 0 or 1
    entry_p = 0
    trades = 0
    mdd = 0
    peak = equity
    
    closes = df['close'].values
    opens = df['open'].values
    rsis = df['rsi'].values
    bb_lows = df['bb_low'].values
    vols = df['volume'].values
    
    waiting_entry = False
    entry_trigger_idx = -1
    
    for i in range(50, len(df)-1):
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak * 100
        mdd = max(mdd, drawdown)
        
        if position == 0:
            if not waiting_entry:
                if rsis[i] < agent['rsi'] and closes[i] < bb_lows[i]:
                    waiting_entry = True
                    entry_trigger_idx = i
            else:
                if i >= entry_trigger_idx + LATENCY:
                    bet = equity * agent['size']
                    vol_val = vols[i] * opens[i] # In simulation units
                    impact = (bet / (vol_val * 1350 + 1e-9)) * IMPACT_FACT
                    actual_entry = opens[i] * (1 + SLIPPAGE + impact)
                    
                    entry_p = actual_entry
                    position = 1
                    waiting_entry = False
                    trades += 1
        else:
            pnl = (closes[i] - entry_p) / entry_p * 100
            if pnl >= agent['tp'] or pnl <= -agent['sl']:
                gross_gain = bet * (pnl/100 - SLIPPAGE)
                if gross_gain > 0: gross_gain *= (1 - TAX)
                equity += gross_gain
                position = 0
                entry_p = 0
    
    return equity, trades, mdd

def run_v2_championship():
    print(f"🏆 TICK-PRECISION CHAMPIONSHIP STARTING (Capital: {INITIAL_CAPITAL:,} KRW)...")
    scenario_dirs = glob.glob("scenarios_v2/*")
    
    final_leaderboard = []
    
    for agent in AGENTS:
        print(f"Testing Agent: {agent['id']}...")
        total_roi_m = 0
        scenario_results = []
        
        for sc_dir in scenario_dirs:
            name = os.path.basename(sc_dir)
            
            # Load the set
            dataset = {
                "1h": pd.read_pickle(f"{sc_dir}/1h.pkl"),
                "D": pd.read_pickle(f"{sc_dir}/D.pkl")
            }
            
            final_eq, trade_count, mdd = simulate_agent_multi_tf(dataset, agent)
            roi_pct = (final_eq - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
            profit_krw = final_eq - INITIAL_CAPITAL
            
            scenario_results.append({
                "scenario": name,
                "profit_krw": profit_krw,
                "roi_pct": roi_pct,
                "mdd": mdd,
                "trades": trade_count,
                "final_equity": final_eq
            })
            total_roi_m += profit_krw / 1_000_000
            
        final_leaderboard.append({
            "agent": agent['id'],
            "total_score_m": total_roi_m,
            "details": scenario_results
        })
        
    final_leaderboard.sort(key=lambda x: x['total_score_m'], reverse=True)
    
    with open("time_machine_v2_results.json", "w") as f:
        json.dump(final_leaderboard, f)
        
    generate_v2_html(final_leaderboard)
    print("✅ V2 CHAMPIONSHIP COMPLETE. Results saved to time_machine_v2_report.html")

def generate_v2_html(results):
    html = f"""
    <html>
    <head>
        <title>Hyper-Precision Time Machine League</title>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; padding: 40px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 20px; border: 1px solid #334155; margin-bottom: 40px; }}
            .agent-card {{ background: #1e293b; border-radius: 15px; padding: 25px; margin-bottom: 30px; border: 1px solid #334155; }}
            h1 {{ color: #38bdf8; margin: 0; }}
            h2 {{ color: #fbbf24; margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ background: #334155; color: #38bdf8; }}
            .profit {{ color: #10b981; font-weight: bold; }}
            .loss {{ color: #ef4444; font-weight: bold; }}
            .mdd {{ color: #f59e0b; }}
            .summary-stat {{ font-size: 1.2rem; font-weight: bold; color: #f8fafc; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 HYPER-PRECISION TIME MACHINE v2</h1>
                <p>Initial Capital: {INITIAL_CAPITAL:,} KRW | 10 Scenarios (Tick-Based) | Multi-Timeframe Awareness</p>
            </div>
    """
    
    for rank, r in enumerate(results):
        html += f"""
        <div class="agent-card">
            <h2>#{rank+1} {r['agent']} <span style="font-size: 0.9rem; color: #94a3b8;">(Total Net: {r['total_score_m']:.2f}M KRW)</span></h2>
            <table>
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Final Balance</th>
                        <th>Profit/Loss (KRW)</th>
                        <th>ROI (%)</th>
                        <th>MDD (%)</th>
                        <th>Trades</th>
                    </tr>
                </thead>
                <tbody>
        """
        for d in r['details']:
            p_class = "profit" if d['profit_krw'] >= 0 else "loss"
            html += f"""
                    <tr>
                        <td><b>{d['scenario'].upper()}</b></td>
                        <td>{d['final_equity']:,.0f}</td>
                        <td class="{p_class}">{d['profit_krw']:+,.0f}</td>
                        <td class="{p_class}">{d['roi_pct']:+.2f}%</td>
                        <td class="mdd">{d['mdd']:.2f}%</td>
                        <td>{d['trades']}</td>
                    </tr>
            """
        html += "</tbody></table></div>"
        
    html += "</div></body></html>"
    with open("time_machine_v2_report.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    run_v2_championship()
