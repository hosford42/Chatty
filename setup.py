from setuptools import setup

setup(
    name='Chatty',
    version='0.0',
    packages=['chatty'],
    url='',
    license='MIT',
    author='Aaron Hosford',
    author_email='hosford42@gmail.com',
    description='Chat bot framework',
    install_requires=[
        'tzlocal',  # MIT
    ],
    extras_require={
        'xmpp': ['sleekxmpp>=1.3', 'dnspython>=1.15'],
        'slack': ['slackclient>=1.2'],
    }
)
