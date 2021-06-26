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


def load_keys():
  KEYS = os.getenv('KEYS_FILENAME')
  book = xlrd.open_workbook(KEYS)
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

def rows_from(excel, ii=None, rown=None):
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
      if rown is not None and x == 0: # rown has meaning only when just one sheet is selected x == 0
        row_range = [rown]
      log.info('Begin sheet name: {}'.format(sh.name))
      for rowx in row_range:
        url = sh.row(rowx)[1] #assumed 1 exists
        if  not url.value:
          log.info('Empty row skyped')
          continue
        pos = '{}__{}__{}__'.format(filenamefy(excel), i, rowx)
        k = scrape.domain(url.value)
        if k in keys:
          yield url.value, {'pos': pos, 'strategy': k, **keys[k]}
        elif arguments.source is None:
          log.info(f'{k} is not on list')
          yield url.value, {'pos': pos, 'strategy': 'all.roses', **{'key':'', 'usr':'', 'pwd':''}}
        if rown is not None:
          return url.value, {'strategy': k, **keys[k]}
  except:
    raise

# keys
try:
  keys = load_keys()
  if arguments.source is not None:
    keys = {k:v for k, v in keys.items() if k in arguments.source}
except Exception as err:
  log.error('Could not load keys', err) 
  sys.exit(1)

async def main():
  # open excel
  try:
    if arguments.only is not None:
      arguments.only = list(set(arguments.only)) 
    await scrape.start(log)
    await scrape.download_using(rows_from(arguments.list, arguments.only, arguments.rownumber))
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
