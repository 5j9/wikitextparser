"""The setup module."""


from setuptools import setup, find_packages
from os import path
from sys import version_info


here = path.abspath(path.dirname(__file__))

install_requires = ['regex', 'wcwidth']
if version_info < (3, 5):
    # Require typing in source distribution
    install_requires.append('typing')

setup(
    name='wikitextparser',
    # Scheme: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    version='0.17.1',
    description='A simple, purely python, WikiText parsing tool.',
    long_description=open(path.join(here, 'README.rst')).read(),
    url='https://github.com/5j9/wikitextparser',
    author='5j9',
    author_email='5j9@users.noreply.github.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    install_requires=install_requires,
    # Require 'typing' in python wheel
    extras_require={"python_version < '3.5'": ['typing']},
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Text Processing',
    ],
    keywords='MediaWiki wikitext parser',
)
