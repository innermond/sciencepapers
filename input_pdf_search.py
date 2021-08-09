import argparse

input = argparse.ArgumentParser(description='given a PDF search for kewords and copy the matching PDF to a target folder')
input.add_argument('-f', '--pdf', type=str, required=True, help='target PDF file')
input.add_argument('-w', '--keywords', type=str, nargs='+', required=True, help='keywords to be searched for')
input.add_argument('-d', '--pdf_directory', type=str, required=True, help='directory path where PDF file will be moved')

arguments = input.parse_args()
if arguments is None:
  raise Exception('No arguments provided')

