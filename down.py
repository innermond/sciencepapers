import sys
import argparse
import xlrd
import scrape
import json

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
            print(f'{i} is not an available sheet index')
            continue
          sh = book.sheet_by_index(i)
          row_range = range(sh.nrows)
          if rown is not None and x == 0: # rown has meaning only when just one sheet is selected x == 0
            row_range = [rown]
          print('sheet name {}'.format(sh.name))
          for rowx in row_range:
              url = sh.row(rowx)[1] #assumed 1 exists
              if  not url.value:
                  print('empty row skyped')
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
  raise Exception('no arguments provided')

# keys
try:
  keys = load_keys()
  if args.source is not None:
    keys = {k:v for k, v in keys.items() if k in args.source}
except Exception as err:
  print('could not load keys', err) 
  sys.exit(1)
 
# open excel
try:
  if args.only is not None:
    args.only = list(set(args.only)) 
  for url in rows_from(args.list, args.only, args.rownumber):
    # here we start to scrape
    print(f'trying to download from: {url}')
except FileNotFoundError as err:
    print('file {} not found'.format(args.list))
    sys.exit(1)
