import os

from setuptools import setup


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, _dirnames, filenames in os.walk('statu'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))

    return packages


setup(name='statu',
      version='0.3.3',
      description='Python State Machines for Humans',
      url='http://github.com/DisruptiveLabs/statu',
      author='Disruptive Labs',
      author_email='pypi@comanage.com',
      install_requires=[
          'six',
      ],
      license='MIT',
      packages=get_packages(),
      zip_safe=False,
      setup_requires=[
          'pytest-runner',
      ],
      tests_require=[
          'pytest',
      ],
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
      ],
      )

