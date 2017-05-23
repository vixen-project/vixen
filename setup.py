import os.path
from setuptools import setup, find_packages

data = {}
fname = os.path.join('vixen', '__init__.py')
exec(compile(open(fname).read(), fname, 'exec'), data)

setup(
    name='vixen',
    version=data.get('__version__'),
    author='Prabhu Ramachandran and Kadambari Devarajan',
    author_email='vixen@googlegroups.com',
    description='View eXtract and aNnotate media',
    url='https://github.com/vixen-project/vixen',
    packages=find_packages(),
    package_dir={'vixen':'vixen'},
    package_data={
        '': ['*.html', '*.css', '*.gif', '*.js']
    },
    include_package_data=True,
    entry_points="""
        [console_scripts]
        vixen = vixen.cli:main
    """
)
