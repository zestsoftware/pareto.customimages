from setuptools import setup, find_packages

version = '1.0'

setup(name='pareto.customimages',
      version=version,
      description="Custom images control panel to override the ones in a design",
      long_description=(open("README.txt").read() + "\n" +
                        open("CHANGES.rst").read()),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 4.3",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          ],
      keywords='custom images',
      author='Thijs Jonkman and Zest Software',
      author_email='info@zestsoftware.nl',
      url='https://github.com/zestsoftware/pareto.customimages',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['pareto'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
