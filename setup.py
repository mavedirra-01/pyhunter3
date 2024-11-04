from setuptools import setup, find_packages

setup(
    name='pyhunter3',
    version='0.1.0',
    description='A tool for testing web applications',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='mavedirra',
    url='https://github.com/mavedirra-01/pyhunter3',
    packages=find_packages(),
    install_requires=[
        'paramiko',
        'colorama',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'pyhunter3=pyhunter3:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
