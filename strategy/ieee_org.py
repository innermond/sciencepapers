import scrape
import asyncio
import contextvars
import os
import cgi
from pathlib import Path
import pyppeteer
import re

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
  pdf_url = await page.evaluate("""async pdf_a => {
    const a = document.querySelector(pdf_a);
    return a.getAttribute('href');
  }""", [pdf_a])
  pdf_url = 'https://ieeexplore.ieee.org' + pdf_url
  direct_access = await page.evaluate("""async pdf_url => {
    return await fetch(pdf_url, { method: 'GET' })
    .then(r => r.text())
  }""", [pdf_url])
  m = re.search('src="(https://ieeexplore.ieee.org/stampPDF/getPDF.jsp[^\"]+)"', direct_access, re.MULTILINE)
  if m is None:
    raise Exception('could not found direct link')
  pdf_url = m.group(1)
  await page._client.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': ctx.collecting_directory})
  arr = await page.evaluate("""async pdf_url => {
    return await fetch(pdf_url, { method: 'GET' })
      .then(r => r.blob())
      .then(b => new Response(b).arrayBuffer())
      .then(t => [...new Uint8Array(t)])
  }""", [pdf_url])
  buf = bytearray(len(arr))
  buf[0:len(arr)] = arr

  fname = os.path.join(ctx.collecting_directory, meta['pos'])+'.pdf'
  with open(fname, 'wb') as w:
    w.write(buf)
    log.info(f'downloaded {fname}')
