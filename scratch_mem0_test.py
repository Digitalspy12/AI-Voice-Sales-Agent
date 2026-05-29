import asyncio
from mem0 import AsyncMemoryClient
from dotenv import load_dotenv

load_dotenv()

async def main():
    memo = AsyncMemoryClient()
    user_name = 'Kundan'
    try:
        results = await memo.get_all(filters={"user_id": user_name})
        print(f"Results type: {type(results)}")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
