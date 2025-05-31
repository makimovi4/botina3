import asyncio
from fake_useragent import UserAgent
from aiohttp import ClientSession
from gettimedelta import get_time_delta
import json
import sqlite3
from datetime import datetime

conn = sqlite3.connect('client.db')
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS proxy (proxy TEXT, last_used INT);")
conn.commit()


class ItemInfo:
    def __init__(self, item_id, item_title, item_price, item_price_currency, item_url, location, country_iso_code,
                 item_view_count, item_time_delta, profile_created_delta, profile_item_count, profile_rating,
                 profile_feedbacks, given_item_count, taken_item_count, profile_url, profile_login, description,
                 item_photo_url):
        self.item_id = item_id
        self.item_title = item_title
        self.item_price = item_price
        self.item_price_currency = item_price_currency
        self.item_url = item_url
        self.location = location
        self.country_iso_code = country_iso_code
        self.item_view_count = item_view_count
        self.item_time_delta = item_time_delta
        self.profile_created_delta = profile_created_delta
        self.profile_item_count = profile_item_count
        self.profile_rating = profile_rating
        self.profile_feedbacks = profile_feedbacks
        self.given_item_count = given_item_count
        self.taken_item_count = taken_item_count
        self.profile_url = profile_url
        self.profile_login = profile_login
        self.description = description
        self.item_photo_url = item_photo_url


def get_new_proxy():
    cur.execute("SELECT * FROM proxy ORDER BY last_used LIMIT 1;")
    proxy_item = cur.fetchone()
    return proxy_item


def update_proxy(proxy_id):
    timestamp = int(datetime.now().replace(microsecond=0).timestamp())
    cur.execute(f"UPDATE proxy SET last_used = {timestamp} WHERE id = {proxy_id}")
    conn.commit()
    # print(f'Updated {proxy} to {timestamp}')


async def get_session(domain_zone, proxy):
    ua = UserAgent(browsers=["firefox"])
    headers = {
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'DNT': '1',
        'Connection': 'keep-alive',
        'TE': 'Trailers',
    }
    session = ClientSession(headers=headers, trust_env=True)
    for i in range(3):
        try:
            req = await session.get(f"http://vinted.{domain_zone}", proxy = proxy, ssl=False)
            page_content = await req.read()
            page_content = page_content.decode('utf-8')
            csrf_token = page_content.split('<meta name="csrf-token" content="')[1].split('"')[0]
            break
        except IndexError:
            await asyncio.sleep(20)
            print(page_content)
            print('__________________________________________________')
            print(f'failed open page {i} times')
            print('__________________________________________________')
    try:
        session.headers['X-CSRF-Token'] = csrf_token
        return session
    except UnboundLocalError:
        return await get_session(domain_zone, proxy)


async def restart_search(parsing_url, session):
    await session.close()
    proxy_item = get_new_proxy()
    update_proxy(proxy_item[0])
    return await run_search(parsing_url, proxy_item[1])


async def run_search(parsing_url, proxy):
    domain_zone = parsing_url[19:]
    domain_zone = domain_zone[:domain_zone.find('/')]
    item_list = []

    session = await get_session(domain_zone, proxy)
    params = (
        ('localize', 'true'),
    )
    # print(datetime.now())
    while True:
        r = await session.get(parsing_url, params=params, proxy=proxy, ssl=False)
        if r.status == 429:
            return await restart_search(parsing_url, session)
        elif r.status != 200:
            print(f'ERROR | Response status: {r.status}')
            print(f'ERROR | Response: {r}')
            # return {'status': r.status}
            return await restart_search(parsing_url, session)
        page_content = (await r.read()).decode('utf-8')
        if '<a href="https://www.google.com/chrome">' not in page_content:
            break
        await asyncio.sleep(1)

    data = json.loads(page_content[page_content.find
                                   ('<script type="application/json" data-js-react-on-rails-store="MainStore">')
                                   + 73:page_content.rfind('}}</script>') + 2])
    if not data['items']['catalogItems']['ids']:
        raise AttributeError
    tasks = []
    new_items = []

    async def get_page_data(item_id):
        item_ps_url = f"https://www.vinted.{domain_zone}/api/v2/items/{item_id}"
        try:
            resp = await session.get(item_ps_url, params=params, proxy=proxy, ssl=False)
            item_data = json.loads(await resp.text())['item']
        except:
            return
        item_title = data['items']['catalogItems']['byId'][str(item_id)]['title']
        item_price = data['items']['catalogItems']['byId'][str(item_id)]['price']
        item_price_currency = data['items']['catalogItems']['byId'][str(item_id)][
            'currency']
        item_url = item_data['url']
        location = item_data['country'] + ", " + item_data['city']
        country_iso_code = item_data['user']['country_iso_code']
        item_view_count = item_data['view_count']
        item_time_delta = get_time_delta(item_data['created_at_ts'])
        # profile_created_delta = get_time_delta(item_data['user']['created_at'])
        profile_created_delta = 0
        profile_item_count = item_data['user']['item_count']
        profile_rating = item_data['user']['feedback_reputation']
        profile_feedbacks = item_data['user']['positive_feedback_count'] + \
                            item_data['user']['neutral_feedback_count'] + \
                            item_data['user']['negative_feedback_count']
        given_item_count = item_data['user']['given_item_count']
        taken_item_count = item_data['user']['taken_item_count']
        profile_url = item_data['user']['profile_url']
        profile_login = item_data['user']['login']
        description = item_data['description']
        if len(description) > 70:
            description = description[:70] + '...'
        try:
            item_photo_url = \
                data['items']['catalogItems']['byId'][str(item_id)]['photo'][
                    'url']
        except TypeError:
            return
        new_item = ItemInfo(item_id, item_title, item_price, item_price_currency,
                            item_url,
                            location,
                            country_iso_code, item_view_count,
                            item_time_delta,
                            profile_created_delta,
                            profile_item_count, profile_rating, profile_feedbacks,
                            given_item_count,
                            taken_item_count, profile_url, profile_login, description,
                            item_photo_url)
        new_items.append(new_item)

    if len(data['items']['catalogItems']) < 10:
        print(data['items']['catalogItems'])
    for item_id in data['items']['catalogItems']['ids']:
        if item_id in item_list:
            continue
        else:
            item_list.append(item_id)
        task = asyncio.create_task(get_page_data(item_id))
        tasks.append(task)
    await asyncio.gather(*tasks)
    await session.close()
    return {'status': r.status, 'data': [item.__dict__ for item in new_items]}


if __name__ == '__main__':
    proxy = get_new_proxy()
    print(proxy)
    update_proxy(proxy[0])
