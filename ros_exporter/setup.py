from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup
d = generate_distutils_setup(
    packages=['ros_exporter'],
    scripts=['ros_exporter.py'],
    package_dir={'': 'src'}
)
setup(**d)