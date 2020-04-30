from setuptools import setup

setup(
        name='snapshotalyzer-30000',
        version='0.1',
        author="James Eubank",
        author_email="jveubank@gmail.com",
        description="SnapshotAlyzer-30000 is a tool to manage AWS EC2 snapshots",
        license="GPLv3+",
        packages=['shotty'],
        url="https://github.com/jveubank/snapshotalyzer-30000",
        install_requires=[
            'click',
            'boto3'
        ],
        entry_points='''
            [console_scripts]
            shotty=shotty.shotty:cli
        ''',
)
