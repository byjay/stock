
import pandas as pd
import json
import logging
import os

logger = logging.getLogger("ISATS_PatternAnalyzer")

class PatternAnalyzer:
    """
    [ISATS AI Core]
    Analyzes 'Winning Patterns' mined by the Elastic Time Machine.
    Derives 'Winning Formulas' (high-probability rules) from the data.
    """
    def __init__(self, data_path=None):
        if data_path:
            self.data_path = data_path
        else:
            # backend/ai/../../data -> isats/data
            self.data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/winning_patterns.jsonl"))
            
    def load_data(self) -> pd.DataFrame:
        """Loads patterns from JSONL into DataFrame."""
        if not os.path.exists(self.data_path):
            logger.warning(f"⚠️ No data found at {self.data_path}")
            return pd.DataFrame()
        
        data = []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except Exception as e:
            logger.error(f"❌ Failed to load patterns: {e}")
            return pd.DataFrame()
            
        return pd.DataFrame(data)

    def generate_formula(self, min_samples=10):
        """
        Analyzes the data and returns a 'Winning Formula'.
        Focuses on:
        1. 2D-RSI and 3D-RSI sweet spots.
        2. MACD Histogram trends in 2D/3D frames.
        """
        df = self.load_data()
        
        if len(df) < min_samples:
            return {"status": "insufficient_data", "count": len(df)}
            
        formula = {
            "version": "2.0 (Deep Genetic)",
            "status": "ready",
            "sample_size": len(df),
            "generated_at": pd.Timestamp.now().isoformat(),
            "rules": {}
        }
        
        # [NEW] Genetic Timeframe Analysis (Fractal Chaos)
        # Identify which custom timeframes (genetic_frames) appear most often in winning patterns
        gene_pool = []
        valid_patterns = df.to_dict('records')
        for p in valid_patterns:
            if 'genetic_frames' in p and isinstance(p['genetic_frames'], list):
                 gene_pool.extend(p['genetic_frames'])
            elif 'genes' in p and isinstance(p['genes'], list): # Legacy support
                 gene_pool.extend(p['genes'])
        
        from collections import Counter
        if gene_pool:
            common_genes = Counter(gene_pool).most_common(5)
            formula["dominant_fractal_genes"] = [g[0] for g in common_genes]
            formula["gene_dominance_score"] = {g[0]: g[1] for g in common_genes}
        
        # 1. RSI Analysis (Sweet Spot)
        # Calculate 25th-75th percentile for RSI in different timeframes
        for frame in ['D', '2D', '3D', '22D']:
            col = f"{frame}_RSI"
            if col in df.columns:
                q25 = df[col].quantile(0.25)
                q75 = df[col].quantile(0.75)
                mean = df[col].mean()
                formula["rules"][col] = {
                    "min": float(q25), 
                    "max": float(q75), 
                    "target": float(mean),
                    "description": f"Best {frame} RSI range: {q25:.1f} ~ {q75:.1f}"
                }

        # 2. MACD Trend
        # Check if MACD_Hist is generally positive or negative before a rise
        # This is a bit simplified, usually we want 'Turnaround' detection.
        # But statistical mean of MACD_Hist can tell us if winners are usually oversold (negative hist) or momentum (positive).
        for frame in ['D', '2D', '3D']:
            col = f"{frame}_MACD_Hist"
            if col in df.columns:
                avg_hist = df[col].mean()
                trend = "Bullish" if avg_hist > 0 else "Bearish Reversal"
                formula["rules"][col] = {
                    "avg_value": float(avg_hist),
                    "trend": trend
                }
                
        return formula

if __name__ == "__main__":
    # Test Run
    analyzer = PatternAnalyzer()
    print(json.dumps(analyzer.generate_formula(), indent=2))
