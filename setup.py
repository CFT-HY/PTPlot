import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ptplot',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'django'
    ],
    include_package_data=True,
    license='MIT License',
    description='PTPlot tool for plotting phase transitions',
    long_description=README,
    url='https://www.ptplot.org/',
    author='David Weir',
    author_email='david.weir@helsinki.fi',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 5.1',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
