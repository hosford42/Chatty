from setuptools import setup, find_packages
import traceback


def get_long_description():
    # noinspection PyBroadException
    try:
        with open('README.md', encoding='utf-8') as file:
            return file.read()
    except Exception:
        traceback.print_exc()
        print("Long description will not be included.")
        return None


# noinspection SpellCheckingInspection
setup(
    name='Chatty',
    version='0.2',
    packages=find_packages(),
    url='https://github.com/hosford42/Chatty',
    download_url='https://pypi.org/project/Chatty',
    license='MIT',
    author='Aaron Hosford',
    author_email='hosford42@gmail.com',
    description='A multi-platform chat bot framework',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    keywords='chat bot chatbot AI artificial intelligence email xmpp IM message text messaging framework slack session '
             'conversation interactive platform multi-platform window local remote protocol',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Email',
        'Topic :: Internet :: XMPP',
        'Topic :: Multimedia',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Text Processing :: Linguistic'
    ],
    install_requires=[
        'tzlocal'  # MIT
    ],
    extras_require={
        'slack': ['slackclient>=1.2'],
        'tkinter': ['tkinter>=8.6'],  # This doesn't come as a built-in package for all platforms.
        'xmpp': ['sleekxmpp>=1.3', 'dnspython>=1.15', 'pyasn1>=0.4', 'pyasn1_modules>=0.2'],
    }
)
