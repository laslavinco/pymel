#!/usr/bin/env mayapy
'''Print out a contents of the core pymel modules in a text format that can be diffed
'''

import sys
import pydoc
import types
import inspect
import os
import argparse
import subprocess

INDENT = 4

THIS_FILE = os.path.normpath(os.path.abspath(inspect.getsourcefile(lambda: None)))
THIS_DIR = os.path.dirname(THIS_FILE)
PYMEL_ROOT = os.path.dirname(THIS_DIR)

DEFAULT_MODULES = ('nodetypes', 'uitypes', 'datatypes', 'general')

def git(arg, output=False):
    if isinstance(arg, basestring):
        args = arg.split()
    else:
        args = arg
    if output:
        func = subprocess.check_output
    else:
        func = subprocess.check_call
    return func(['git'] + list(args), cwd=PYMEL_ROOT)

def gitout(arg):
    return git(arg, output=True).rstrip()

def githash(branch='HEAD'):
    return gitout(['show', '-s', '--format=%H', branch])

def printobj(name, obj, prefix='', depth=0, file=sys.stdout):
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        try:
            spec = inspect.getargspec(obj)
            sig = inspect.formatargspec(*spec)
        except:
            sig = '(<error>)'
        # file.write((' ' * (depth * INDENT)) + name + sig + '\n')
        file.write(prefix + name + sig + '\n')
    else:
        # file.write((' ' * (depth * INDENT)) + name + '\n')
        file.write(prefix + name + '\n')

    # print depth, isinstance(obj, (type, types.ModuleType))
    if (depth < 2 and isinstance(obj, type)) or (depth == 0 and isinstance(obj, types.ModuleType)):
        childprefix = prefix + name + '.'
        for childname in sorted(dir(obj)):
            try:
                child = getattr(obj, childname)
            except:
                child = None
            printobj(childname, child, prefix=childprefix, depth=depth + 1, file=file)

def writemods(branch, output, modules=None):
    git(['checkout', branch])
    hash = githash()
    if hash != branch:
        commit = '{}-{}'.format(branch, hash)
    else:
        commit = hash
    if not os.path.isdir(output):
        os.makedirs(output)
    if not modules:
        modules = DEFAULT_MODULES
    for modname in modules:
        fullnames = (modname, 'pymel.core.' + modname)
        for fullname in fullnames:
            try:
                mod = __import__(fullname, globals(), locals(), [''])
                break
            except Exception:
                pass
        else:
            raise RuntimeError("failed to import module {!r} or {!r}"
                               .format(*fullnames))
        mod = __import__(fullname, globals(), locals(), [''])
        print mod
        path = os.path.join(output, '%s@%s.txt' % (fullname, commit))
        with open(path, 'w') as f:
            printobj(fullname, mod, file=f)

def getparser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-b', '--branch', default='master',
        help='git branch to checkout (and add to output filenames)')
    parser.add_argument('-o', '--output-dir', default='pymel_modules',
        help="Directory to which to write out pymel module information")
    parser.add_argument('-m', '--module', dest='modules', action='append',
        help="What pymel modules to print out; may be specified multiple times"
             " to specify multiple modules; modules should be specified using"
             " the import name (ie, 'pymel.core.nodetypes'); if a module fails"
             " to import, it will assume it is in 'pymel.core' (so you may just"
             " use 'nodetypes'); if not given at all, the default set of"
             " modules is: {}".format(', '.join(DEFAULT_MODULES)))
    parser.add_argument('--traceback', action='store_true',
        help="If given, will print full tracebacks on errors")
    return parser

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = getparser()
    args = parser.parse_args(argv)
    try:
        writemods(args.branch, args.output_dir, modules=args.modules)
    except Exception as e:
        if args.traceback:
            raise
        print e
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())