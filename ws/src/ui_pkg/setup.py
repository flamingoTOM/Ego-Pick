from setuptools import setup
from glob import glob

package_name = 'ui_pkg'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User',
    maintainer_email='user@example.com',
    description='Ego-Pick main UI package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'main_ui_node = ui_pkg.main_ui:main',
        ],
    },
)
