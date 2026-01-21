import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ParameterManager")

class ParameterManager:
    """
    [ISATS V1.1] Deep Learning Parameter Manager
    Loads best hyperparameters from .json result files and serves them to strategies.
    Ensures that the latest learning results are always integrated into live trading.
    """
    def __init__(self, results_dir: str = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if results_dir is None:
            self.results_dir = os.path.join(base_dir, "data", "learning_results")
        else:
            self.results_dir = results_dir
            
        self.model_path = os.path.join(base_dir, "data", "current_strategy_model.json")
        self.params_cache: Dict[str, Any] = {}
        self.load_all_results()

    def load_all_results(self):
        """Scan results directory and load valid JSON parameters."""
        # 1. Load Legacy/Batch Results
        if os.path.exists(self.results_dir):
            for filename in os.listdir(self.results_dir):
                if filename.endswith(".json"):
                    path = os.path.join(self.results_dir, filename)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            self.params_cache[filename] = json.load(f)
                    except Exception: pass

        # 2. Load Active Deep Learning Model (Priority)
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "r", encoding="utf-8") as f:
                    self.params_cache["current_model"] = json.load(f)
                logger.info("✅ [Deep Learning] Active Strategy Model Loaded.")
            except Exception as e:
                logger.error(f"Failed to load active model: {e}")

    def get_best_gene(self) -> Dict[str, Any]:
        """Returns the best gene, prioritizing the Infinite Learner."""
        # 1. Check Infinite Learner
        model = self.params_cache.get("current_model")
        if model and "gene" in model:
            g = model["gene"]
            return {
                "ma_window": g.get("ema_filter", 20),
                "vol_threshold": g.get("rsi_entry", 30), # Mapping RSI to context
                "sl_pct": g.get("sl_pct", 2.0),
                "tp_pct": g.get("tp_pct", 5.0),
                "source": "INFINITE_LOOP"
            }
            
        # 2. Fallback to Batch Results
        data = self.params_cache.get("best_genes_v2.json")
        if data and "gene" in data:
            return {
                "ma_window": data["gene"][0],
                "use_filter": data["gene"][1],
                "vol_threshold": data["gene"][2],
                "score": data.get("score")
            }
        return {}

    def get_agent_params(self, agent_id: str) -> List[Dict[str, Any]]:
        """Returns parameter set for a specific million_agent (e.g., '01_Scalp')"""
        filename = f"million_agent_{agent_id}.json"
        return self.params_cache.get(filename, [])

    def refresh(self):
        """Reload all parameters from disk."""
        self.load_all_results()
