import logging
import time
from typing import List, Dict

logger = logging.getLogger("ConditionHandler")

class ConditionHandler:
    def __init__(self, kiwoom_wrapper):
        self.kiwoom = kiwoom_wrapper
        self.conditions: List[Dict] = []
        self.active_conditions: Dict[str, int] = {} # {name: index}

    def load_conditions(self):
        """Triggers the loading of conditions from Kiwoom."""
        logger.info("Loading HTS Conditions...")
        self.kiwoom.get_condition_load()
        # Note: We need to wait for _on_receive_condition_ver callback in the wrapper.
        # In a full AsyncTask implementation, we'd use a Future or Event.
        
    def start_monitoring(self, target_conditions: List[str]):
        """
        Starts real-time monitoring for specific condition names.
        target_conditions: List of condition names (e.g. ["GoldCross", "N-Pattern"])
        """
        # Fetch latest list (assuming load_conditions completed)
        raw_list = self.kiwoom.get_condition_name_list()
        self.conditions = raw_list
        logger.info(f"Available Conditions: {[c['name'] for c in self.conditions]}")
        
        for target in target_conditions:
            found = next((c for c in self.conditions if c['name'] == target), None)
            if found:
                index = found['index']
                logger.info(f"Registering Real-time Condition: {target} (Idx: {index})")
                # Screen number strategy: 1000 + index (simple allocation)
                screen_no = str(1000 + index)
                self.kiwoom.send_condition(screen_no, target, index, 1) # 1 = Realtime
                self.active_conditions[target] = index
            else:
                logger.warning(f"Condition '{target}' not found in HTS list.")

    def stop_monitoring(self):
        # Implementation for stopping would go here (SendConditionStop)
        pass
