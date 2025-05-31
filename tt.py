import asyncio
from aiohttp import ClientSession


async def start():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'DNT': '1',
        'Connection': 'keep-alive',
        'TE': 'Trailers',
    }
    async with ClientSession() as s:
        response = await s.get(
            "http://vinted.cz", headers=headers
        )
        print(response.status)
asyncio.run(start())