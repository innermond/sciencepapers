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


def rows_from(excel):
  try:
      book = xlrd.open_workbook(excel)
      names = book.sheet_names()
      for name in names:
          print('sheet name {}'.format(name))
          sh = book.sheet_by_name(name)
          for rowx in range(sh.nrows):
              url = sh.row(rowx)[1] #assumed 1 exists
              if  not url.value:
                  print('empty row skyped')
                  continue
              key = scrape.domain(url.value)
              if key in keys:
                yield url.value
  except:
    raise


# get list
input = argparse.ArgumentParser(description="Get a PDF's list and download them")
input.add_argument('-l', '--list', type=str, help='list filepath')
args = input.parse_args()
if args is None:
  raise Exception('no arguments provided')

# keys
try:
  keys = load_keys()
except Exception as err:
  print('could not load keys', err) 
  sys.exit(1)
 
# open excel
try:
  for url in rows_from(args.list):
    # here we start to scrape
    print(f'trying to download from: {url}')
except FileNotFoundError as err:
    print('file {} not found'.format(args.list))
    sys.exit(1)
