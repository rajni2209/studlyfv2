import asyncio
from db import submissions_col

async def main():
    count = await submissions_col.count_documents({})
    print(f"Total submissions: {count}")

if __name__ == '__main__':
    asyncio.run(main())
