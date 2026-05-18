import asyncio

from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    from src.app import start

    asyncio.run(start())
