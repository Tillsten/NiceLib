# -*- coding: utf-8 -*-
# Copyright 2016-2018 Nate Bogdanowicz
import os
import os.path
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install as _install
from setuptools.command.sdist import sdist as _sdist
from setuptools.command.develop import develop as _develop

description = ('A package for rapidly developing "nice" Python bindings to C libraries, '
               'using `cffi`')
classifiers = [
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.13',
    'Programming Language :: Python :: 3.14',
    'Programming Language :: Python :: 3.15',
]

# Load metadata from __about__.py
base_dir = os.path.dirname(__file__)
readme_path = os.path.join(base_dir, 'README.rst')
about_path = os.path.join(base_dir, 'nicelib', '__about__.py')
about = {}
with open(about_path) as f:
    exec(f.read(), about)

install_requires = [
    'cffi>=1.5',
    'pycparser',
]


# Pre-generate tables within the package, just as pycparser does
def _run_build_tables(dir):
    from subprocess import call
    path = os.path.join(dir, 'nicelib', 'parser')
    print('Running _build_tables.py on path "{}"'.format(path))
    call([sys.executable, '_build_tables.py'],
         cwd=path)


class install(_install):
    def run(self):
        _install.run(self)
        self.execute(_run_build_tables, (self.install_lib,), msg="Build the lexing/parsing tables")


class sdist(_sdist):
    def make_release_tree(self, basedir, files):
        _sdist.make_release_tree(self, basedir, files)
        self.execute(_run_build_tables, (basedir,), msg="Build the lexing/parsing tables")


class develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_run_build_tables, (self.setup_path,), msg="Build the lexing/parsing tables")


if __name__ == '__main__':
    setup(
        name = about['__distname__'],
        version = about['__version__'],
        packages = find_packages(),
        author = about['__author__'],
        author_email = about['__email__'],
        description = description,
        long_description = '\n'.join(open(readme_path).read().splitlines()[2:]),
        url = about['__url__'],
        license = about['__license__'],
        python_requires = '>=3.13',
        classifiers = classifiers,
        install_requires = install_requires,
        cmdclass={'install': install, 'sdist': sdist, 'develop': develop},
    )
