import sys
import logging
import xlrd
import scrape
import json
import os
import re
import unicodedata
import asyncio
import signal
import itertools

from dotenv import load_dotenv
load_dotenv()

from input import arguments

# logging
log = logging.getLogger('app')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(os.getenv('LOGGER_FORMAT'))
ch.setFormatter(formatter)
log.addHandler(ch)

KEYS = os.getenv('KEYS_FILENAME')

def load_keys(fn):
  book = xlrd.open_workbook(fn)
  sh = book.sheet_by_index(0)
  
  keys = {}
  for rowx in range(sh.nrows):
    domain, key, usr, pwd = sh.row(rowx)
    keys[domain.value] = {'key': key.value.strip(), 'usr': usr.value.strip(), 'pwd': pwd.value.strip()}
  return keys

def filenamefy(value, allow_unicode=False):
  value = str(value)
  if allow_unicode:
    value = unicodedata.normalize('NFKC', value)
  else:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub(r'[^\w\s-]', '', value.lower())
  return re.sub(r'[-\s]+', '-', value).strip('-_')

def rows_from(excel, ii=None, rown=None, source=None):
  try:
    book = xlrd.open_workbook(excel)
    
    natural_range = range(0, book.nsheets)
    if ii is None:
      ii = natural_range
    for x, i in enumerate(ii):
      if i not in natural_range:
        log.error(f'Sheet index {i} is not available in the current workbook')
        continue
      
      sh = book.sheet_by_index(i)
      row_range = range(sh.nrows)
      
      # adjust row_range for rown
      if rown is not None and x == 0: # rown has meaning only when just one sheet is selected x == 0
        if rown not in row_range:
          log.error(f'{rown} is not in worksheet range')
          break
        row_range = [rown]

      log.info('Begin sheet name: {}'.format(sh.name))
      for rowx in row_range:
        url = sh.row(rowx)[1] #assumed 1 exists
        if  not url.value:
          log.info('Empty row skyped')
          continue

        pos = '{}__{}__{}__'.format(filenamefy(excel), i, rowx)
        k = scrape.domain(url.value)

        # row number is above all
        if rown is not None:
          if k in keys:
            yield url.value, {'pos': pos, 'strategy': k, **keys[k]}
            break
          if os.getenv('UNKNOWN_SOURCE_TRY') == '1':
            log.info(f'{k} is not on list -- trying')
            yield url.value, {'pos': pos, 'strategy': 'all.roses', **{'key':'', 'usr':'', 'pwd':''}}
            break
          else:
            log.info(f'{k} is not on list -- skipping')
            break

        # dealing with source
        has_source = source is not None
        if has_source and k not in source: continue
        
        if k in keys:
          yield url.value, {'pos': pos, 'strategy': k, **keys[k]}
        else:
          if os.getenv('UNKNOWN_SOURCE_TRY') == '1':
            log.info(f'{k} is not on list -- trying')
            yield url.value, {'pos': pos, 'strategy': 'all.roses', **{'key':'', 'usr':'', 'pwd':''}}
          else:
            log.info(f'{k} is not on list -- skipping')
  except:
    raise

# keys
try:
  keys = load_keys(KEYS)
  if arguments.source is not None:
    keys = {k:v for k, v in keys.items() if k in arguments.source}
except Exception as err:
  log.error(f'Could not load keys from {KEYS}') 
  sys.exit(1)

async def main():
  # open excel
  try:
    # keep unique values
    if arguments.only is not None:
      arguments.only = list(set(arguments.only)) 
    if arguments.source is not None:
      arguments.source = list(set(arguments.source)) 
    rows = rows_from(arguments.list, arguments.only, arguments.rownumber, arguments.source)
    rows, rows1 = itertools.tee(rows, 2)
    lrows = sum(1 for i in rows1)
    log.info(f'Counts: {lrows}')
    if arguments.count is True: return
    await scrape.start(log)
    i=0
    peak_retries = 3
    while i < peak_retries:
      retries = await scrape.download_using(rows)
      if len(retries) == 0: break
      rows = retries
      await asyncio.sleep(1)
      i += 1
    else:
      log.error(f'retried {peak_retries} times to download')
      for url in [u for u,_ in retries]:
        log.error(f'{url} NOT downloaded')

  except FileNotFoundError as err:
    log.error('File {} not found'.format(arguments.list))
    raise err
  except Exception as err:
    log.error('main: ', err)
    raise err
  except KeyboardInterrupt as e:
    raise e
  finally:
    await scrape.end()

if __name__ == '__main__':

  try:
    def signal_handler(sig, frame):
      raise KeyboardInterrupt('kill them all')
    signal.signal(signal.SIGINT, signal_handler)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
  except KeyboardInterrupt as e:
    log.error('canceling request from user - finishing pending operations...')
    if loop.is_running():
      tasks = asyncio.gather(*asyncio.all_tasks(loop=loop), loop=loop, return_exceptions=True)
      tasks.add_done_callback(lambda t: loop.stop())
      tasks.cancel()
      while not tasks.done() and not loop.is_closed():
        loop.run_forever()
      loop.run_until_complete(loop.shutdown_asyncgens())
      loop.close()
