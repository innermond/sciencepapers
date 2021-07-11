import scrape
import asyncio
import contextvars
import os
import cgi
from pathlib import Path
import pyppeteer

ctx_authenticated = contextvars.ContextVar('authenticated')
ctx_authenticated.set(False)

async def apply(ctx, url, meta):
  #import pyppeteer
  #import random
  #if random.randint(2, 5)%2==1: raise pyppeteer.errors.TimeoutError('artificial error')
  # shorts
  log = ctx.log
  page = ctx.page
  log.info(f'{__name__} [{url}] in progress...')
  if not ctx_authenticated.get('authenticated'):
    home_url = 'https://ieeexplore.ieee.org/Xplore/home.jsp'
    await page.goto(home_url)
    # click on institutional sign
    is_selector = 'xpl-login-modal-trigger a'
    await page.waitForSelector(is_selector)
    institutional_a = await page.querySelector(is_selector)
    if institutional_a is None:
      log.error('Could not find "Institutional Sign"')
      return
    await institutional_a.click()
    # choose University of Melbourne
    univ_selector = 'xpl-inst-typeahead input'
    inst_selector = 'xpl-inst-typeahead a'
    await page.waitForSelector(univ_selector)
    await page.type(univ_selector, 'University of Melbourne')
    await page.waitForSelector(inst_selector)
    await page.click(inst_selector)
    await page.waitForNavigation()
    btn_selector = '#okta-signin-submit'
    await page.waitForSelector(btn_selector)
    await page.type('input[name=username]', meta['usr'])
    await page.type('input[name=password]', meta['pwd'])
    await asyncio.wait([
      page.click(btn_selector),
      page.waitForNavigation(),
    ])
    await page.waitForSelector('img')
    ctx_authenticated.set(True)

  # to the target
  await asyncio.wait([
    page.goto(url),
    page.waitForNavigation({'waitUntil': 'load'}),
  ])
  pdf_a = 'xpl-view-pdf a'
  await page.waitForSelector(pdf_a, {'visible': True})
  await page._client.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ctx.collecting_directory})
  await page.click(pdf_a)
  resp = await page.waitForResponse(response_adjuster)
  tx = resp.headers.get('x-filename')
  log.info(f'original filename to download: {tx}')
  if tx is not None:
    tmp = os.path.join(ctx.collecting_directory, tx)
    ext = Path(tmp).suffix
    ext_mime = os.getenv('DOWNLOAD_TYPE')
    ext_mime = ext_mime.split('/')[-1]
    if ext == '.'+ext_mime:
      timeout = int(os.getenv('CHECK_DOWNLOAD_SECONDS', 30))
      await asyncio.wait_for(check_downloading(tmp), timeout)
      fnm = os.path.join(ctx.collecting_directory, meta['pos'] + ext)
      try:
        os.rename(tmp, fnm)
        log.info(f'downloaded as {fnm}')
      except Exception as ex:
        log.error(ex)
        log.info(f'renaming failure: download saved as {tx}')
    else:
      raise pyppeteer.errors.TimeoutError

def response_adjuster(res):
  ctyp = res.headers.get('content-disposition') 
  if ctyp is not None:
    value, params = cgi.parse_header(ctyp)
    res.headers['x-filename'] = params['filename']
    return True
  return False

async def check_downloading(p):
  while not os.path.exists(p): pass
