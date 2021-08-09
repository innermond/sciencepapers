from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
import io
import os
import logging

from input_pdf_search import arguments

# logging
log = logging.getLogger('app')
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(os.getenv('LOGGER_FORMAT'))
ch.setFormatter(formatter)
log.addHandler(ch)

if __name__ == '__main__':
  fp = open(arguments.pdf, 'rb')
  rsrcmgr = PDFResourceManager()
  retstr = io.StringIO()
  codec = 'utf-8'
  laparams = LAParams()
  device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)

  page_no = 0
  for pageNumber, page in enumerate(PDFPage.get_pages(fp)):
    interpreter.process_page(page)
    data = retstr.getvalue()
    data = data.encode('utf-8')
    print(data, page_no)
    #with open(os.path.join('Files/Company_list/0010/text_parsed/2017AR', f'pdf page {page_no}.txt'), 'wb') as file:
     # file.write(data.encode('utf-8'))
    data = ''
    retstr.truncate(0)
    retstr.seek(0)

    page_no += 1
