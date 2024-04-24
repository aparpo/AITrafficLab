import setuptools

#Si tienes un readme
with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
     name='AITrafficLab', 
     version='0.1', 
     scripts=[] , 
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
 )