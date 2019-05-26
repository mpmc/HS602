# Copyright (C) 2019 Mark Clarkstone <mpmc@disroot.org>
#
# This file is part of hs602.
#
# hs602 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hs602 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hs602.  If not, see <http://www.gnu.org/licenses/>.
import hs602
from setuptools import setup, find_packages
setup(
    name='hs602',
    version=hs602._version_,
    description='HS602 utilities.',
    keywords='HS602, capture, streaming, broadcasting, rtmp',
    author='Mark Clarkstone',
    author_email='mpmc@disroot.org',
    url='https://github.com/mpmc/hs602',
    license='GPL-3.0',
    python_requires='>=3.3',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'hs602-example=hs602.example:main',
        ]
    },
    install_requires=[''],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Other Audience',
        'Topic :: Internet',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Graphics :: Capture',
        'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3 :: Only',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
)
