import setuptools

#Si tienes un readme
with open("README.md", "r") as fh:
    long_description = fh.read()

# Leer el archivo requirements.txt
def read_requirements():
    with open('requirements.txt') as reqs:
        return reqs.read().splitlines()

setuptools.setup(
     name='AITrafficLab', 
     version='0.3', 
     author="Alvaro Martinez Parpolowicz", 
     author_email="alvaro.parpolowicz@live.u-tad.com.com",
     description="Un paquete para entrenar modelos de optimizacion del trafico basados en sistemas multiagente.",
     long_description=long_description,
     long_description_content_type="text/markdown", 
     url="https://github.com/aparpo/AITrafficLab",
     packages=setuptools.find_packages(), 
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     install_requires = [
        "matplotlib>=3.8.3",
        "mesa>=2.3.0",
        "networkx>=3.2.1",
        "numpy>=1.26.4",
        "osmnx>=1.9.3",
        "scipy>=1.13.1",
        "setuptools>=69.5.1",
        "sumolib>=1.19.0",
        "tqdm>=4.66.2",
        "traci>=1.20.0",
     ]
 )