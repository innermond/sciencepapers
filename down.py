import sys
import argparse
import xlrd
import scrape
import json

# get list
input = argparse.ArgumentParser(description="Get a PDF's list and download them")
input.add_argument('-l', '--list', type=str, help='list filepath')
args = input.parse_args()
if args is None:
  raise Exception('no arguments provided')

# keys
with open('keys.json') as k:
    keys = json.loads(k.read())
print(keys)
# open excel
try:
    book = xlrd.open_workbook(args.list)
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
            print(key)
        
except FileNotFoundError as err:
    print('file {} not found'.format(args.list))
    sys.exit(1)
print(args)
