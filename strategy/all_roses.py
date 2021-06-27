import requests
import scrape
import os
import mimetypes

async def apply(ctx, url, meta):
  ctx.log.info(f'{__name__} [{url}] in progress...')
  tc = int(os.getenv('TIMEOUT_CONNECT'))
  tr = int(os.getenv('TIMEOUT_RESPONSE'))
  raise requests.exceptions.HTTPError('aaaa')
  r = requests.head(url, allow_redirects=True, timeout=(tc,tr))
  ctyp = r.headers.get('content-type')
  if ctyp is None:
    ctx.log.error('server did not provided expected header...skipping')
    return
  ctx.log.info(f'{ctyp} for {url}')
  chop = ctyp.find(';')
  if chop > -1:
    ctyp = ctyp[0:chop]
  if ctyp == os.getenv('DOWNLOAD_TYPE'):
    ext = mimetypes.guess_extension(ctyp)
    if not ext:
      ext = '.pdf'
    fname = os.path.join(ctx.collecting_directory, meta['pos'])+ext
    ctx.log.info(f'try to download as {fname}')
    with requests.get(url, allow_redirects=True, timeout=(tc, tr)) as r:
      r.raise_for_status()
      with open(fname, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
          f.write(chunk)
      ctx.log.info(f'downloaded {fname}')
