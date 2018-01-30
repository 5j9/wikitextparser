"""Setup wikitextparser."""


from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))

setup(
    name='wikitextparser',
    # Scheme: [N!]N(.N)*[{a|b|rc}N][.postN][.devN]
    version='0.18.0',
    description='A simple parsing tool for MediaWiki\'s wikitext markup.',
    long_description=open(path.join(here, 'README.rst')).read(),
    url='https://github.com/5j9/wikitextparser',
    author='5j9',
    author_email='5j9@users.noreply.github.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(exclude='tests'),
    python_requires='>=3.3',
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Text Processing',
    ],
    keywords='MediaWiki wikitext parser',
)
