import aiohttp
import asyncio
import yaml
import os

# ==========================================
# 📡 TACTICAL MESSENGER (텔레그램 알림)
# ==========================================

class TelegramBot:
    def __init__(self):
        self.token = ""
        self.chat_id = ""
        self._load_config()

    def _load_config(self):
        """secrets.yaml에서 토큰을 불러옵니다."""
        try:
            # 상위 폴더의 config/secrets.yaml 탐색
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "config", "secrets.yaml")
            
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    telegram = data.get('telegram', {})
                    self.token = telegram.get('token', '')
                    self.chat_id = telegram.get('chat_id', '')
        except Exception as e:
            print(f"⚠️ [Notifier] 설정 로드 실패: {e}")

    async def send(self, message):
        """메시지 전송 (비동기)"""
        if not self.token or not self.chat_id:
            print(f"   📢 [Ferrari Intel] {message}")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"🏎️ *[Ferrari Intel]*\n\n{message}",
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        res_text = await resp.text()
                        print(f"⚠️ 텔레그램 전송 실패: {resp.status} - {res_text}")
        except Exception as e:
            print(f"⚠️ 텔레그램 오류: {e}")

# 테스트 실행
if __name__ == "__main__":
    bot = TelegramBot()
    if not bot.token:
        print("❌ [Notice] secrets.yaml에 'telegram: token/chat_id' 설정이 없습니다.")
        print("   -> 콘솔 모드로 작동합니다.")
    
    asyncio.run(bot.send("작전 구역 투입 준비 완료. (Connectivity OK)"))
