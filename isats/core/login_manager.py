import sys
from PyQt5.QtWidgets import QApplication
from backend.core.kiwoom_wrapper import KiwoomWrapper
import logging

logger = logging.getLogger("LoginManager")

class LoginManager:
    def __init__(self):
        self.app = None
        self.kiwoom = None

    def connect(self):
        """Initializes QApplication and Kiwoom Connection."""
        # PyQt5 requires a QApplication instance
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()

        self.kiwoom = KiwoomWrapper()
        
        logger.info("Starting Kiwoom Login Sequence...")
        self.kiwoom.comm_connect()
        
        # Verify connection
        if self.kiwoom.get_login_info("GetServerGubun"): # Returns 1 for Mock/Simulation, Empty for Real
            logger.info("Login confirmed.")
            accounts = self.kiwoom.get_login_info("ACCNO")
            logger.info(f"Available Accounts: {accounts}")
            return True
        else:
            logger.warning("Login verification status unclear or failed.")
            return False

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    manager = LoginManager()
    manager.connect()
