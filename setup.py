from setuptools import setup

setup(
    name='Chatty',
    version='0.0',
    packages=['chatty'],
    url='https://github.com/hosford42/Chatty',
    license='MIT',
    author='Aaron Hosford',
    author_email='hosford42@gmail.com',
    description='Chat bot framework',
    install_requires=[
        'tzlocal',  # MIT
    ],
    extras_require={
        'slack': ['slackclient>=1.2'],
        'tkinter': ['tkinter>=8.6'],  # This doesn't come as a built-in package for all platforms.
        'xmpp': ['sleekxmpp>=1.3', 'dnspython>=1.15'],
    }
)
