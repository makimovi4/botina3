import asyncio
from datetime import datetime
from aiohttp import web

from pars_funcs import run_search

search_count = 0


async def handle(request):
    global search_count
    search_count += 1
    current_id = search_count
    print(f'Started. Search id {current_id}')
    parsing_url = request.query['parsing_url']
    now = datetime.now()
    while True:
        try:
            result = await run_search(parsing_url, None)
            break
        except OSError:
            continue
    if result['status'] != 200:
        print(f'result={result}')
    print(f'time for search: {datetime.now() - now}| {parsing_url=} items={len(result["data"])}| id={current_id}')
    return web.json_response(result)

app = web.Application()
app.add_routes([web.post('/search', handle)])

if __name__ == '__main__':
    web.run_app(app)
