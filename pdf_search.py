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
import shutil
import logging

from input_pdf_search import arguments

if __name__ == '__main__':
  # logging
  log = logging.getLogger('app')
  log.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  formatter = logging.Formatter(os.getenv('LOGGER_FORMAT'))
  ch.setFormatter(formatter)
  log.addHandler(ch)

  # validate
  if os.path.isfile(arguments.pdf) == False:
    log.error('%s is not a file', arguments.pdf)
    sys.exit(1)
  if os.path.isdir(arguments.directory) == False:
    log.error('%s is not a directory', arguments.directory)
    sys.exit(1)

  fp = open(arguments.pdf, 'rb')
  rsrcmgr = PDFResourceManager()
  retstr = io.StringIO()
  codec = 'utf-8'
  laparams = LAParams()
  device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)

  page_no = 0
  pattern = '\s+'.join(map(lambda n: re.escape(n), arguments.keywords))
  directory = os.path.abspath(arguments.directory)
  copied = os.path.join(directory, os.path.basename(arguments.pdf))
  if arguments.overwrite and os.path.isfile(copied):
    log.error('there is already a file "%s"', copied)
    sys.exit(1)

  for pageNumber, page in enumerate(PDFPage.get_pages(fp)):
    interpreter.process_page(page)
    page_no += 1
    data = retstr.getvalue()
    log.info('page %s', page_no)
    found = re.search(pattern, data, re.IGNORECASE)
    if found:
      log.info('found "%s", now copying to directory "%s"', pattern, directory)
      # check file is there
      try:
        shutil.copy(os.path.abspath(arguments.pdf), directory)
        log.info('successfully copied "%s"', copied)
        sys.exit(0)
      except Exception as ex:
        log.error('error %s', ex)
        sys.exit(1)
    else:
      log.info('did not found "%s"', pattern)
    data = ''
    retstr.truncate(0)
    retstr.seek(0)
