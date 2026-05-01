from setuptools import setup
import os
from glob import glob

package_name = 'encoder_pkg'

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
    description='JY-ME01 Encoder driver package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'encoder_node = encoder_pkg.encoder_pub:main',
            'encoder_plot_node = encoder_pkg.encoder_plot:main',
        ],
    },
)
