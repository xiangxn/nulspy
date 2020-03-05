from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

about = {}
with open(os.path.join(here, 'nulspy', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name='nulspy',
    version=os.getenv('BUILD_VERSION', about['__version__']),
    description='Python library for the NULS API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Necklace',
    author_email='xnxiangxn@hotmail.com',
    url='https://github.com/xiangxn/nulspy',
    license="MIT",
    packages=find_packages(),
    test_suite='nose.collector',
    install_requires=[
        'coincurve'
    ])
