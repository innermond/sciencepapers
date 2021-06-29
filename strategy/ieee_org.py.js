import scrape
import asyncio
import contextvars
import os

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
  pdf_url = await page.evaluate("""async pdf_a => {
    const a = document.querySelector(pdf_a);
    return a.getAttribute('href');
  }""", [pdf_a])
  pdf_url = 'https://ieeexplore.ieee.org' + pdf_url
  await asyncio.wait([
    page.goto(pdf_url),
    page.waitForSelector('iframe'),
  ])

  pdf_url = await page.evaluate("""async () => {
    const p = new Promise((result, reject) => {
      const xf = document.querySelector('iframe');
      console.log(xf);
      const tid = setInterval(()=>{
        const src = xf.contentWindow.document.location.href;
        if (src) {
          result(src);
          clearInterval(tid);
        }  
      }, 2000);
      console.log(tid);
    });
    console.log(p)
    return await p;
  }""")

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
  #await asyncio.wait([
   # page.click(pdf_a),
   # page.waitForNavigation({'waitUntil': 'load'}),
  #])
