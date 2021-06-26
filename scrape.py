import sys
from urllib.parse import urlparse
import asyncio
from pyppeteer import launch
from importlib import import_module
import time
import os
from pathlib import Path

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
  except Exception as e:
    ctx.log.error(e)
    return False

ctx = type('', (), {})()
ctx.log=None
ctx.browser=None
ctx.page=None
ctx.collecting_directory=None

def collecting_directory_create():
  # create directory
  n = 0
  directory_tries = 3
  directory_name = os.path.join(os.getenv('COLLECTING_DIRECTORY'), time.strftime('%Y.%m.%d.%H.%M.%S'))
  directory_name = os.path.realpath(directory_name)
  while n < directory_tries:
    try:
      Path(directory_name).mkdir(parents=True, exist_ok=True)
      break
    except Exception as e:
      n = n + 1
      time.sleep(1)
      directory_name = os.path.join(os.getenv('COLLECTING_DIRECTORY'), time.strftime('%Y.%m.%d.%H.%M.%S'))
      directory_name = os.path.realpath(directory_name)
  if n == directory_tries:
    raise Exception('exhausted tries allowed to create a collecting directory')
  return directory_name


async def start(logger):
  ctx.log = logger
  ctx.browser = await launch({
    'headless': True, 
    'autoClose': False, 
    'handleSIGINT': False, 
    })
  ctx.page = await ctx.browser.newPage()
  ctx.collecting_directory = collecting_directory_create()

async def end():
  if ctx.page.isClosed == False: await ctx.page.close()
  await ctx.browser.close()

async def download_using(urls):
  toplevel_prev = ''
  for url, meta in urls:
    toplevel = domain(url)
    try:
      if toplevel == toplevel_prev:
        ctx.log.info('applied rate limit')
        time.sleep(1)
      strategy_namespace = import_strategy(meta['strategy'])
      # strategy
      if strategy_namespace == False:
        ctx.log.info('No strategy yet for %s' % toplevel)
        s_none = os.getenv('STRATEGY_NONE')
        if s_none is None: 
          continue
        else:
          strategy_namespace = import_strategy(s_none)
          if strategy_namespace == False:
            ctx.log.info('No strategy "%s" found' % s_none)
            continue

      strategy = sys.modules[strategy_namespace]
      await strategy.apply(ctx, url, meta)
    except Exception as err:
      ctx.log.error('scrape:', err)
    except KeyboardInterrupt as ke:
      raise ke

    toplevel_prev = domain(url)
    continue
