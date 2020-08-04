"""Setup wikitextparser."""


from setuptools import setup, find_packages
from os.path import abspath, dirname, join


here = abspath(dirname(__file__))

setup(
    name='wikitextparser',
    version='0.42.2',
    description='A simple parsing tool for MediaWiki\'s wikitext markup.',
    long_description=open(join(here, 'README.rst'), encoding='utf8').read(),
    url='https://github.com/5j9/wikitextparser',
    author='5j9',
    author_email='5j9@users.noreply.github.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.5',
    install_requires=['regex', 'wcwidth'],
    extras_require={'dev': ['path.py', 'coverage', 'twine']},
    tests_require=['pytest'],
    zip_safe=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Text Processing'],
    keywords='MediaWiki wikitext parser')
