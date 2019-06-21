
pip install nose
pip install numpy
pip install scipy
pip install cython
pip install biopython
pip install pyparsing

#Installation de ProDy
cd ${LIGHTDOCK_HOME}/ProDy
sudo python setup.py build
sudo python setup.py install

#Installation freesasa
cd ${LIGHTDOCK_HOME}/freesasa
sudo python setup.py build
sudo python setup.py install

