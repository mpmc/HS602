#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2017 Mark Clarkstone <git@markclarkstone.co.uk>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  setup.py
#
#  Copyright 2017 Mark Clarkstone <git@markclarkstone.co.uk>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from setuptools import setup
setup(
    name='hs602',
    version='0.2.0.dev1',
    description='A simple HS602 (capture device) controller and tools.',
    keywords='HS602 capture, streaming, broadcasting, rtmp',
    author='Mark Clarkstone',
    author_email='git@markclarkstone.co.uk',
    url='https://github.com/mpmc/hs602',
    license='GPL-3.0',
    python_requires='>=3.3',
    install_requires=[],
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
