import os.path
from setuptools import setup, find_packages

data = {}
fname = os.path.join('vixen', '__init__.py')
exec(compile(open(fname).read(), fname, 'exec'), data)

classes = """
Development Status :: 5 - Production/Stable
Environment :: Web Environment
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: End Users/Desktop
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Topic :: Scientific/Engineering :: Information Analysis
Topic :: Utilities
"""

classifiers = [x.strip() for x in classes.splitlines() if x]

requires = [
    'traits',
    'jigna',
    'tornado<5.0',
    'json_tricks>=3.0',
    'whoosh',
    'backports.csv'
]

tests_require = [
    'mock',
    'pytest'
]

setup(
    name='vixen',
    version=data.get('__version__'),
    author='Prabhu Ramachandran and Kadambari Devarajan',
    author_email='vixen@googlegroups.com',
    description='View eXtract and aNnotate media',
    long_description=open('README.md').read(),
    url='https://github.com/vixen-project/vixen',
    classifiers=classifiers,
    install_requires=requires,
    tests_require=tests_require,
    packages=find_packages(),
    package_dir={'vixen': 'vixen'},
    package_data={
        '': ['*.html', '*.css', '*.gif', '*.js']
    },
    include_package_data=True,
    entry_points="""
        [console_scripts]
        vixen = vixen.cli:main
    """
)
