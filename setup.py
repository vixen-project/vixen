import os.path
from setuptools import setup, find_packages

data = {}
execfile(os.path.join('vixen', '__init__.py'), data)

setup(
    name='vixen',
    version=data.get('__version__'),
    author='Prabhu Ramachandran and Kadambari Devarajan',
    description='View eXtract and aNnotate media',
    packages=find_packages(),
    package_dir={'vixen':'vixen'},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        vixen = vixen.cli:main
    """
)
