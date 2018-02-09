"""Setup wikitextparser."""


from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from re import search, MULTILINE


here = abspath(dirname(__file__))

setup(
    name='wikitextparser',
    version=search(
        r'^__version__ = [\'"]([^\'"]*)[\'"]',
        open(
            join(here, 'wikitextparser', '__init__.py'), encoding='utf8'
        ).read(),
        MULTILINE,
    ).group(1),
    description='A simple parsing tool for MediaWiki\'s wikitext markup.',
    long_description=open(join(here, 'README.rst'), encoding='utf8').read(),
    url='https://github.com/5j9/wikitextparser',
    author='5j9',
    author_email='5j9@users.noreply.github.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(exclude='tests'),
    python_requires='>=3.4',
    install_requires=[
        'regex',
        'wcwidth',
        'typing;python_version<"3.5"',
    ],
    zip_safe=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Text Processing',
    ],
    keywords='MediaWiki wikitext parser',
)
