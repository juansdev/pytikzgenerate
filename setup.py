from distutils.core import setup
from os.path import join, dirname
from pytikz import Pytikz

__version__ = Pytikz.__version__

def get_description():
    with open(join(dirname(__file__), 'README.md'), 'rb') as fileh:
        return fileh.read().decode("utf8").replace('\r\n', '\n')

setup(
    name='Pytikz',
    version=__version__,
    author='Juan Guillermo Serrano Ramirez',
    author_email='juanfater2017@gmail.com',
    url='https://github.com/juansdev',
    license='MIT',
    description=(
        'Una libreria de software para el rapido desarrollo de '
        'graficos utilizando el codigo TiKZ.'),
    long_description=get_description(),
    long_description_content_type='text/markdown',
    packages=["pytikz"],
    package_dir={'pytikz': 'pytikz'},
    download_url = 'https://github.com/{user_name}/{repo}/tarball/0.1',
    classifiers=[
        'Development Status :: 0.2.0 - Alpha',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: MIT License',
        'Natural Language :: Spanish',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Artistic Software',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Scientific/Engineering :: Visualization',
        ('Topic :: Software Development :: Libraries')])