import asyncio
import os
import sys

# 페라리 경로 추가
sys.path.append(os.path.abspath("ISATS_Ferrari"))

from core.engine import FerrariEngine

async def main():
    print("🚀 [ISATS v2.5] Operation Ferrari: Systems Online.")
    engine = FerrariEngine()
    await engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🏁 [ISATS] Operation Terminated by Commander.")
