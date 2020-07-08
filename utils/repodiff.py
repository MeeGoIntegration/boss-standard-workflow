#!/usr/bin/python3 -tt
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# (c) 2007 Red Hat. Written by skvidal@fedoraproject.org

import sys
from optparse import OptionParser
import repo_diff

def parseArgs():
    """
       Parse the command line args. return a list of 'new' and 'old' repos
    """
    usage = """
    repodiff: take 2 or more repositories and return a list of added, removed and changed
              packages.
 
    repodiff --old=old_repo_baseurl --new=new_repo_baseurl """
    
    parser = OptionParser(version = "repodiff 0.2", usage=usage)
    # query options
    parser.add_option("-n", "--new", default=[], action="append",
                      help="new baseurl[s] for repos")
    parser.add_option("-o", "--old", default=[], action="append",
                      help="old baseurl[s] for repos")
    parser.add_option("-q", "--quiet", default=False, action='store_true')
    parser.add_option("-a", "--archlist", default=[], action="append",
                      help="In addition to src.rpms, any arch you want to include")
    parser.add_option("-s", "--size", default=False, action='store_true',
                      help="Output size changes for any new->old packages")
    parser.add_option("-r", "--rebuilds", default=False, action='store_true',
                      help="Output Rebuild stats")
    parser.add_option("-c", "--commits", default=False, action='store_true',
                      help="Output count of OBS commits")
    parser.add_option("--short", default=False, action='store_true',
                      help="Only report added, removed and modified package names")
    (opts, _) = parser.parse_args()

    if not opts.new or not opts.old:
        parser.print_usage()
        sys.exit(1)

    archlist = ['src']
    for a in opts.archlist:
        for arch in a.split(','):
            archlist.append(arch)

    opts.archlist = archlist

    return opts

if __name__ == "__main__":
    if not sys.stdout.isatty():
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

    opts = parseArgs()

    try:
        if opts.short:
            report = repo_diff.generate_short_diff(opts.new, opts.old)
        else:
            report = repo_diff.generate_report(opts.new, opts.old, quiet=opts.quiet,
                                               archlist=opts.archlist, size=opts.size,
                                               rebuilds=opts.rebuilds, commits=opts.commits)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    
    print(report)
    sys.exit(0)

