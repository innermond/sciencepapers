from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
import io
import re
import os
import sys
import logging
import hashlib
import asyncio
from concurrent.futures import ProcessPoolExecutor

from input_pdf_keyword_paragraph import arguments

# logging
log = logging.getLogger('app')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(os.getenv('LOGGER_FORMAT'))
ch.setFormatter(formatter)
log.addHandler(ch)

# collect all interested files
def get_files(ext):
  files = []
  currentfile = arguments.pdf
  if os.path.isdir(currentfile):
    os.chdir(currentfile)
    for root, _, founds in os.walk('.'):
      if len(founds) == 0: continue
      founds = filter(lambda f: f.endswith(ext), founds)
      founds = map(lambda f: os.path.join(root, f), founds)
      files.extend(founds)
  elif os.path.isfile(currentfile):
      files.append(currentfile)
  else:
    log.error('%s is not a file, nor a directory', currentfile)
    sys.exit(1)
  return files

def process_page(currentfile, pageNumber, page, dp):
  peek_lines = arguments.peek
  pattern = '\s+'.join(map(lambda n: re.escape(n), arguments.keywords))
  pattern = r'{}'.format(pattern)
  codec = 'utf-8'
  laparams = LAParams()
  rsrcmgr = PDFResourceManager()
  retstr = io.StringIO()
  device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)
  interpreter.process_page(page)
  
  data = retstr.getvalue()
  opt = 0
  if arguments.ignorecase is True:
    opt = re.IGNORECASE
  ff = re.finditer(pattern, data, opt)
  par = []
  hashes = set()
  for found in ff:
    a = found.start()
    z = found.end()
    left = data[:a]
    m = re.search(r'.*\n\n', left, re.DOTALL)
    y1 = 0
    if m is not None:
      y1 = m.end()
    #peek left
    if peek_lines > 0:
      left = data[y1:a]
      left_num = left.count('\n')
      diff = left_num - peek_lines
      if diff > 0:
        mm = re.finditer(r'\n', left)
        for n,m in enumerate(mm):
          if n == diff-1: 
            y1 = y1 + m.end()
            break
    y2 = len(data)
    right = data[z:]
    m = re.search(r'.*\n\n', right)
    if m is not None:
      y2 = z + m.end()
    #peek right
    if peek_lines > 0:
      right = data[z:y2]
      right_num = right.rstrip('\n').count('\n')
      diff = right_num - peek_lines
      if diff > 0:
        mm = re.finditer(r'\n', right)
        for n,m in enumerate(mm):
          if n == peek_lines: 
            y2 = z + m.end()
            break
    txt = data[y1:y2].rstrip()
    
    hx = hashlib.md5(txt.encode()).hexdigest()
    if hx in hashes:
      continue
    hashes.add(hx)
    par.append(txt)
  if len(par) > 0: 
    times = len(par)
    log.info('File %s - found %s times in page %s', currentfile, times, pageNumber+1)
    if arguments.title:
      title = 'Page {} keyword "{}" found {} times'.format(pageNumber+1, raw_keywords, times)
      dp.write('{}\n{}\n'.format(title, len(title)*'-'))
    dp.write('\n\n'.join(par) + '\n\n')
  else: 
    log.info('File %s - not found in page %s',currentfile, pageNumber+1)
  data = ''
  retstr.truncate(0)
  retstr.seek(0)


# workhorse here!!
def find_into(currentfile):
  log.info('opening file {}'.format(currentfile))
  fp = open(currentfile, 'rb')

  raw_keywords = ' '.join(arguments.keywords)
  postfix = '-'.join(arguments.keywords)+'.txt'
  noext = os.path.splitext(currentfile)[0]
  doc = os.path.abspath(noext+'_'+arguments.document+'_'+postfix)
  if arguments.overwrite and os.path.isfile(doc):
    log.error('there is already a file "%s"', doc)
    return

  with open(doc, 'w') as dp:
    dp.write('File: {}\n\n'.format(currentfile))
    for pageNumber, page in enumerate(PDFPage.get_pages(fp)):
      process_page(currentfile, pageNumber, page, dp)

loop = asyncio.get_event_loop()

async def main():
  files = get_files('.pdf')
  with ProcessPoolExecutor() as executor:
    for currentfile in files:
      loop.run_in_executor(executor, find_into, currentfile)

if __name__ == '__main__':
  loop.run_until_complete(main())
