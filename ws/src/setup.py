from setuptools import setup
import os
from glob import glob

setup(
    name='encoder_pkg',
    version='1.0.0',
    packages=['scripts'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/encoder_pkg/']),
        ('share/encoder_pkg/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User',
    maintainer_email='user@example.com',
    description='JY-ME01 Encoder driver package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'encoder_node = scripts.read_encoder:main',
            'encoder_plot_node = scripts.encoder_plot:main',
        ],
    },
)
