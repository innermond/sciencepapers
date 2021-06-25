import sys
from urllib.parse import urlparse
import asyncio
from pyppeteer import launch
from importlib import import_module
import requests
import time

def domain(url: str, ld=2) -> str:
    d = urlparse(url).netloc
    d = d.split('.')
    if len(d) > ld:
        d = d[-ld:]
    d = '.'.join(d)
    return d.strip()

# load dinamically a strategy
def import_strategy(lib):
  #lib is a website topdomain
  lib = 'strategy.%s' % lib.replace('.', '_')
  # already imported?
  if lib in sys.modules:
    return lib
  try:
    sys.modules[lib] = import_module(lib)
    return lib
  except:
    return False

ctx = type('', (), {})()
ctx.log=None
ctx.browser=None
ctx.page=None


async def start(logger):
  ctx.log = logger
  ctx.browser = await launch()
  #ctx.browser = await launch({'headless': False})
  ctx.page = await ctx.browser.newPage()

async def end():
  await ctx.browser.close()

async def download(urls):
  toplevel_prev = ''
  for url, meta in urls:
    toplevel = domain(url)
    try:
      if toplevel == toplevel_prev:
        ctx.log.info('applied rate limit')
        time.sleep(1)
      #r = requests.get(url, timeout=(3,3))
      #ctyp = r.headers['content-type']
      #ctx.log.info(f'{ctyp} for {url}')
    except requests.exceptions.Timeout:
      ctx.log.error('timeouted')
    finally:
      toplevel_prev = domain(url)
      continue
    strategy_namespace = import_strategy(meta['strategy'])
    # strategy
    if strategy_namespace == False:
      ctx.log.info('No strategy yet for %s' % toplevel)
      continue
    strategy = sys.modules[strategy_namespace]
    await strategy.apply(ctx, url)
