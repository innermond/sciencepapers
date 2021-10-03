import argparse

input = argparse.ArgumentParser(description='Given a keyword, search pdfs and copy the paragraph surrounding the keyword into a document, with the title of the source')
input.add_argument('-f', '--pdf', type=str, required=True, help='target PDF file')
input.add_argument('-w', '--keywords', type=str, nargs='+', required=True, help='keywords to be searched for')
input.add_argument('-d', '--document', type=str, required=True, help='document name, to collect all paragraphs of interest')

input.add_argument('-i', '--ignorecase', default=False, dest='ignorecase', action='store_true', help='searching case insensitive')

input.add_argument('-t', '--title', default=False, dest='title', action='store_true', help='add a title for every founds on page')

input.add_argument('-x', '--overwrite', default=False, dest='overwrite', action='store_true', help='overwrite an already-there document paragraphs collector')

input.add_argument('-k', '--peek', type=int, default=0, help='num of lines up and down arround found keyword')

arguments = input.parse_args()
if arguments is None:
  raise Exception('No arguments provided')

