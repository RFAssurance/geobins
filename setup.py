from distutils.core import setup

setup(
    name='geobin',
    version='0.1',
    author='Wen-Jann Yang',
    author_email='wyang@ttswireless.com',
    url='https://github.com/RFAssurance/geobins',
    description='Create universal hexbins',
    keywords=['hexbin', 'bins', 'coordinate', 'conversion'],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    packages=['geobin'],
    scripts=['scripts/geobin-converter'],
)
