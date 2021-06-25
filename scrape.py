from urllib.parse import urlparse
import asyncio
from pyppeteer import launch

def domain(url: str, ld=2) -> str:
    d = urlparse(url).netloc
    d = d.split('.')
    if len(d) > ld:
        d = d[-ld:]
    d = '.'.join(d)
    return d.strip()

state = type('', (), {})()
state.log=None
state.browser=None
state.page=None


async def start(logger):
  state.log = logger
  state.browser = await launch()
  state.page = await state.browser.newPage()

async def end():
  await state.browser.close()

async def download(urls):
  for url in urls:
    state.log.info(f'Trying to download from: {url}')
    await state.page.goto(url)
    state.log.info('download: headless is on page %s' % url)
    await state.page.screenshot({'path': './sample.png'})
