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
    'args': ['--no-sandbox'],
    'ignoreDefaultArgs': ["--enable-automation"],
    })
  ctx.page = await ctx.browser.newPage()
  userAgent = 'Mozilla/5.0 (X11; Linux x86_64)A ppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.39 Safari/537.36'
  await ctx.page.setUserAgent(userAgent)
  await ctx.page.evaluateOnNewDocument("""() => {

  Object.defineProperty(navigator, 'webdriver', {
    get: () => false,
  });};

  Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
  });

  Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
  });

  window.navigator.chrome = {
    app: {
      isInstalled: false,
    },
    webstore: {
      onInstallStageChanged: {},
      onDownloadProgress: {},
    },
    runtime: {
      PlatformOs: {
        MAC: 'mac',
        WIN: 'win',
        ANDROID: 'android',
        CROS: 'cros',
        LINUX: 'linux',
        OPENBSD: 'openbsd',
      },
      PlatformArch: {
        ARM: 'arm',
        X86_32: 'x86-32',
        X86_64: 'x86-64',
      },
      PlatformNaclArch: {
        ARM: 'arm',
        X86_32: 'x86-32',
        X86_64: 'x86-64',
      },
      RequestUpdateCheckStatus: {
        THROTTLED: 'throttled',
        NO_UPDATE: 'no_update',
        UPDATE_AVAILABLE: 'update_available',
      },
      OnInstalledReason: {
        INSTALL: 'install',
        UPDATE: 'update',
        CHROME_UPDATE: 'chrome_update',
        SHARED_MODULE_UPDATE: 'shared_module_update',
      },
      OnRestartRequiredReason: {
        APP_UPDATE: 'app_update',
        OS_UPDATE: 'os_update',
        PERIODIC: 'periodic',
      },
    },
  };

    const originalQuery = window.navigator.permissions.query;
  return window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
      Promise.resolve({ state: Notification.permission }) :
      originalQuery(parameters)
  );
  """)
  ctx.collecting_directory = collecting_directory_create()

async def end():
  pass
  #if ctx.page.isClosed == False: await ctx.page.close()
  #await ctx.browser.close()

async def download_using(urls):
  toplevel_prev = ''
  for url, meta in urls:
    toplevel = domain(url)
    try:
      if toplevel == toplevel_prev:
        slowdown = int(os.getenv('SLOWDOWN', '2'))
        ctx.log.info(f'applied rate limit {slowdown} seconds')
        time.sleep(slowdown)

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
    except KeyboardInterrupt as ke:
      raise ke
    except Exception as err:
      ctx.log.error(f'scrape: {url} cannot be downloaded')
      if os.getenv('LOGGER_SHOW_ERROR', '0') == '1':
        ctx.log.error('scrape:', err)

    toplevel_prev = domain(url)
    continue
