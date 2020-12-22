
from setuptools import setup, find_packages
import pathlib

this_directory = pathlib.Path(__file__).parent
with open(this_directory / 'README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'pianoputer',
    install_requires = ['librosa >= 0.8.0', 'pygame >= 2.0.0', 'keyboardlayout >= 2.0.0'],
    python_requires='>=3',
    version = '2.0.0',
    description = 'Use your computer keyboard as a "piano"',
    author = 'Zulko',
    maintainer='Justin Black',
    packages = find_packages(),
    include_package_data=True,
    url = "https://github.com/Zulko/pianoputer",
    entry_points = {
        'console_scripts': ['pianoputer=pianoputer.pianoputer:play_pianoputer'],
    },
    license='see LICENSE.txt',
    keywords = ["piano", "keyboard", "synthesizer"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    extras_require={
        'dev': [
            'setuptools',
            'wheel',
            'twine',
        ]
    },
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Games/Entertainment :: Simulation',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Players'
    ],
    long_description = long_description
)
