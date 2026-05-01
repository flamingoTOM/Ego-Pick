from setuptools import setup
from glob import glob

package_name = 'imu_pkg'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User',
    maintainer_email='user@example.com',
    description='WitMotion IMU ROS2 driver',
    license='MIT',
    entry_points={
        'console_scripts': [
            'imu_node = imu_pkg.imu_node:main',
            'qt_imu_viewer = imu_pkg.qt_imu_viewer:main',
        ],
    },
)
