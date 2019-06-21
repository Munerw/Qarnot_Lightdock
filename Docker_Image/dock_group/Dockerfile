# Use an official Python runtime as a parent image
FROM python:2.7

# On copie l'ensemble du programme dans le fichier de travail
COPY . /prog

#Installation des dépendances
RUN pip install nose
RUN pip install numpy
RUN pip install scipy
RUN pip install cython
RUN pip install biopython
RUN pip install pyparsing

#Installation de ProDy
WORKDIR /prog/ProDy
RUN python setup.py build
RUN python setup.py install

#Installation freesasa
WORKDIR /prog/freesasa
RUN python setup.py build
RUN python setup.py install

WORKDIR /prog
ENV LIGHTDOCK_HOME=../prog
ENV LIGHTDOCK_BIN=../prog/bin/
ENV LIGHTDOCK_LIB=$LIGHTDOCK_BIN/../
ENV PYTHONPATH=$PYTHONPATH:$LIGHTDOCK_BIN:$LIGHTDOCK_LIB

ENTRYPOINT []
