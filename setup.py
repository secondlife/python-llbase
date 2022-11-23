import os

from setuptools import find_packages, setup

root_dir = os.path.dirname(__file__)
with open(os.path.join(root_dir, "README.md")) as f:
    long_description = f.read()


setup(
    name='llbase',
    url='https://github.com/secondlife/python-llbase',
    description='Base Linden Lab Python modules',
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms=['any'],
    packages=find_packages(exclude=('tests',)),
    license='MIT',
    install_requires=['requests', 'llsd'],
    extras_require={
        "dev": ["pytest", "mock", "pytest-cov<3"],
    },
    setup_requires=["setuptools_scm<6"],
    use_scm_version={
        'local_scheme': 'no-local-version', # disable local-version to allow uploads to test.pypi.org
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
    ],
)