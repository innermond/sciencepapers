import scrape
import asyncio
import contextvars
import os
import cgi
from pathlib import Path

ctx_authenticated = contextvars.ContextVar('authenticated')
ctx_authenticated.set(False)

async def apply(ctx, url, meta):
  # shorts
  log = ctx.log
  page = ctx.page
  log.info(f'{__name__} [{url}] in progress...')
  if not ctx_authenticated.get('authenticated'):
    home_url = 'https://ieeexplore.ieee.org/Xplore/home.jsp'
    await ctx.page.goto(home_url)
    # click on institutional sign
    is_selector = 'xpl-login-modal-trigger a'
    await page.waitForSelector(is_selector)
    institutional_a = await ctx.page.querySelector(is_selector)
    if institutional_a is None:
      ctc.log.error('Could not find "Institutional Sign"')
      return
    await institutional_a.click()
    # choose University of Melbourne
    univ_selector = 'xpl-inst-typeahead input'
    inst_selector = 'xpl-inst-typeahead a'
    await page.waitForSelector(univ_selector)
    await page.type(univ_selector, 'University of Melbourne')
    await page.waitForSelector(inst_selector)
    #await page.waitFor(1000)
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
  log.info(f'redirect to {url}')
  await asyncio.wait([
    page.goto(url),
    page.waitForNavigation({'waitUntil': 'load'}),
  ])
  pdf_a = 'xpl-view-pdf a'
  await page.waitForSelector(pdf_a)
  await page._client.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ctx.collecting_directory})
  await page.click(pdf_a)
  resp = await page.waitForResponse(response_adjuster)
  tx = resp.headers.get('x-filename')
  if tx is not None:
    tmp = os.path.join(ctx.collecting_directory, tx)
    await check_downloading(tmp)
    ext = Path(tmp).suffix
    fnm = os.path.join(ctx.collecting_directory, meta['pos'] + ext)
    try:
      os.rename(tmp, fnm)
    except:
      log.info(f'renaming failure: download saved as {tx}')

def response_adjuster(res):
  ctyp = res.headers.get('content-disposition') 
  if ctyp is not None:
    value, params = cgi.parse_header(ctyp)
    res.headers['x-filename'] = params['filename']
    return True
  return False

async def check_downloading(p):
  p = Path(p).stem
  down = p + '.crdownload'
  keepon = 0
  while True:
    if os.path.exists(p): break
    if keepon > 10: break
    if os.path.exists(down): keepon = 0
    await asyncio.sleep(1)
    keepon += 1
