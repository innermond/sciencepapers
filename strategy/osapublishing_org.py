import scrape
import asyncio
import contextvars
import os
from pathlib import Path
import pyppeteer
import re

ctx_authenticated = contextvars.ContextVar('authenticated')
ctx_authenticated.set(False)

async def apply(ctx, url, meta):
  # shorts
  log = ctx.log
  page = ctx.page
  log.info(f'{__name__} [{url}] in progress...')
  if not ctx_authenticated.get('authenticated'):
    home_url = 'https://www.osapublishing.org'
    await page.goto(home_url,  {"waitUntil" : "networkidle0"})
    # accept cookies - has effect?
    is_selector = '#cookiePopup a.btn-primary'
    cookie_a = await page.waitForSelector(is_selector, {'visible': True})
    await cookie_a.click()
    # wait for cookie panel to dissapeat and UNCOVER our link. Remember, we are a human user, we cannot click on covered elements
    await page.waitForSelector(is_selector, {'hidden': True})
    # click on login
    is_selector = '#loginModal'
    login_a = await page.waitForSelector(is_selector, {'visible': True})
    if login_a is None:
      log.error('Could not find "login link"')
      return
    await login_a.click()
    is_selector = '#userLogin div.modal-footer div:first-child a'
    institutional_a = await page.waitForSelector(is_selector, {'visible': True})
    if institutional_a is None:
      log.error('Could not find "Institutional Sign"')
      return
    href = await page.evaluate('e=>e.href', institutional_a)
    await page.goto(href,  {"waitUntil" : "networkidle0"})
    # choose University of Melbourne
    univ_selector = '#typeahead'
    inst_selector = 'table tr:last-child'
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
  if 'viewmedia.cfm' not in url:
    await asyncio.wait([
      page.goto(url),
      page.waitForNavigation({'waitUntil': 'load'}),
    ])
    pdf_sel = 'a[href*="viewmedia.cfm"]'
    pdf_a = await page.waitForSelector(pdf_sel, {'visible': True})
    pdf_url = await page.evaluate("""async pdf_a => {
      const a = document.querySelector(pdf_a);
      return a.getAttribute('href');
    }""", [pdf_sel])
    pdf_url = 'https://www.osapublishing.org/' + pdf_url
  else:
    # when accesing by viewmedia.cfm
    direct_access = await page.evaluate("""async pdf_url => {
      return await fetch(pdf_url, { method: 'GET' })
      .then(r => r.text())
    }""", [url])
    m = re.search('src="(https://www.osapublishing.org/DirectPDFAccess/[^\"]+)"', direct_access, re.MULTILINE)
    if m is None:
      raise Exception('could not found direct link')
    pdf_url = m.group(1)
    await asyncio.wait([
      page.goto(url),
      page.waitForNavigation({'waitUntil': 'load'}),
    ])

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
