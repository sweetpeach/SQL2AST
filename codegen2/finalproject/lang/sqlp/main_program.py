import parser
from optparse import OptionParser
import sys, os.path, itertools, glob
import pprint

#o = OptionParser()
#o.add_option('--regen', action='store_true', dest='regen', default=False,
#       help="Regenerate SQL Parser cache")
#o.add_option('--debug', action='store_true', dest='debug', default=False,
#       help="Enable debug")
#options, args = o.parse_args()
#files = args[0:] if args else None

# The only thing special about a regen is that there are no input files.
#if options.regen:
  # Delete the lex/yacc files.  Ply is too stupid to regenerate them
  # properly
#  for fileglobs in [os.path.join('./sqlp', f) for f in ["sqlplex.py*", "sqlpyacc.py*"]]:
#    for filename in glob.glob(fileglobs):
#      os.remove(filename)

# Instantiate the parser.
p = parser.SQLParser()#debug=options.debug)


parsed_result = [p.parse("SELECT this_column FROM That_Table;")]
pprint.pprint(parsed_result)
