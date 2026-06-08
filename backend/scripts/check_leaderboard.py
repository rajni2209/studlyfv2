import asyncio
from db import leaderboard_col

async def main():
    data = await leaderboard_col.find({}).to_list(length=5)
    print(f"Leaderboard items: {len(data)}")
    for item in data:
        print(item)

if __name__ == '__main__':
    asyncio.run(main())
