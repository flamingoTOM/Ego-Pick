from setuptools import setup
from glob import glob

package_name = 'stereo_pkg'

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
    description='Stereo camera package',
    license='MIT',
    entry_points={
        'console_scripts': [
            'stereo_camera_node = stereo_pkg.stereo_pub:main',
            'stereo_viewer_node = stereo_pkg.stereo_viewer:main',
            'main_node = stereo_pkg.main_ui:main',
        ],
    },
)
