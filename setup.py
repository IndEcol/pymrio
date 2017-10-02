from setuptools import setup

exec(open('pymrio/version.py').read())

setup(
    name='pymrio',
    description=(
        'A python module for automating input output '
        'calculations and generating reports'),
    long_description=open('README.rst').read(),
    url='https://github.com/konstantinstadler/pymrio',
    author='Konstantin Stadler',
    author_email='konstantin.stadler@ntnu.no',
    version=__version__,  # noqa
    packages=['pymrio', ],
    install_requires=['pandas >= 0.17.0'],
    classifiers=[
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3 :: Only',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
          'Topic :: Utilities',
          ],
)
