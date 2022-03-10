import setuptools

with open("README.txt", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='multipagetiff',
                 version='3.0.7',
                 description='open multipage tiff stacks and create z-projections',
                 author='Marco Pascucci',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 author_email='marpas.paris@gmail.com',
                 url='https://github.com/mpascucci/multipagetiff',
                 packages=setuptools.find_packages(),
                 install_requires=['numpy', 'matplotlib', 'tqdm'],
                 classifiers=[
                     "Programming Language :: Python",
                     "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
                     "Operating System :: OS Independent",
                 ]
                 )
