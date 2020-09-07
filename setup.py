"""Setup script for the python-act library module"""

from os import path

from setuptools import setup

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), "rb") as f:
    long_description = f.read().decode('utf-8')

setup(
    name="act-scio",
    version="0.0.19",
    author="mnemonic AS",
    zip_safe=True,
    author_email="opensource@mnemonic.no",
    description="ACT SCIO",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT",
    keywords="ACT, mnemonic",
    entry_points={
        'console_scripts': [
            'scio-analyze = act.scio.analyze:main',
            'scio-api = act.scio.api:main',
            'scio-config = act.scio.scio_config:main',
            'scio-feeds = act.scio.feeds.feeds:main',
            'scio-tika-server = act.scio.tika_engine:main',
            'scio-nltk-download= act.scio.nltk_download:main',
            'scio-upload = act.scio.upload:main',
        ]
    },

    # Include ini-file(s) from act/workers/etc
    package_data={'act.scio': ['etc/*', 'etc/plugins/*', 'vendor/*']},
    packages=["act.scio", "act.scio.plugins", "act.scio.feeds"],

    # https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages
    # __init__.py under all packages under in the act namespace must contain exactly string:
    # __path__ = __import__('pkgutil').extend_path(__path__, __name__)
    namespace_packages=['act'],
    url="https://github.com/mnemonic-no/act-scio2",
    install_requires=[
        "addict",
        "aiofiles",
        "beautifulsoup4",
        "bs4",
        "caep",
        "elasticsearch",
        "elasticsearch_dsl",
        "fastapi",
        "feedparser",
        "greenstalk>=2.0.0",
        "ipaddress",
        "justext",
        "nltk",
        "pytest-asyncio",
        "pytest",
        "python-magic",
        "requests",
        "tika",
        "urllib3",
        "uvicorn",
    ],
    python_requires='>=3.6, <4',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: ISC License (ISCL)",
    ],
)
