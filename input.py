import argparse

# get list
input = argparse.ArgumentParser(description="Get a PDF's list and download them")
input.add_argument('-l', '--list', type=str, required=True, help='list filepath')
input.add_argument('-o', '--only', type=int, nargs='+', default=None, help="use only sheets selected by position, first sheet is 0")
input.add_argument('-s', '--source', type=str, nargs='+', default=None, help='use only sources indicated, must be top domain - ieee.org, not explore.ieee.org')
input.add_argument('-r', '--rownumber', type=int, default=None, help='row position in sheet file, work just when only a sheet is selected  - first row is at 0 position')
input.add_argument('-c', '--count', default=False, dest='count', action='store_true', help='just count the records')
arguments = input.parse_args()
if arguments is None:
  raise Exception('No arguments provided')

