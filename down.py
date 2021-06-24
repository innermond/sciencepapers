import sys
import logging
import argparse
import xlrd
import scrape
import json

# logging
log = logging.getLogger('app')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)


def load_keys():
  KEYS = 'keys.xls'
  book = xlrd.open_workbook(KEYS)
  sh = book.sheet_by_index(0)
  
  keys = {}
  for rowx in range(sh.nrows):
    domain, key, usr, pwd = sh.row(rowx)
    keys[domain.value] = {'key': key.value.strip(), 'usr': usr.value.strip(), 'pwd': pwd.value.strip()}
  return keys


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
        key = scrape.domain(url.value)
        if key in keys:
          yield url.value
        if rown is not None:
          return url.value
  except:
    raise

# get list
input = argparse.ArgumentParser(description="Get a PDF's list and download them")
input.add_argument('-l', '--list', type=str, required=True, help='list filepath')
input.add_argument('-o', '--only', type=int, nargs='+', default=None, help="use only sheets selected by position, first sheet is 0")
input.add_argument('-s', '--source', type=str, nargs='+', default=None, help='use only sources indicated, must be top domain - ieee.org, not explore.ieee.org')
input.add_argument('-r', '--rownumber', type=int, default=None, help='row position in sheet file, work just when only a sheet is selected  - first row is at 0 position')
args = input.parse_args()
if args is None:
  raise Exception('No arguments provided')

# keys
try:
  keys = load_keys()
  if args.source is not None:
    keys = {k:v for k, v in keys.items() if k in args.source}
except Exception as err:
  log.error('Could not load keys', err) 
  sys.exit(1)
 
# open excel
try:
  if args.only is not None:
    args.only = list(set(args.only)) 
  for url in rows_from(args.list, args.only, args.rownumber):
    # here we start to scrape
    log.info(f'Trying to download from: {url}')
except FileNotFoundError as err:
  log.error('File {} not found'.format(args.list))
  sys.exit(1)
