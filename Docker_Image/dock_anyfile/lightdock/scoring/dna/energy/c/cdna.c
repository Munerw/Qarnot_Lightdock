#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include "structmember.h"
#include "numpy/arrayobject.h"


#define EPSILON 4.0
#define FACTOR 332.0
#define MAX_ES_CUTOFF 1.0
#define MIN_ES_CUTOFF -1.0
#define VDW_CUTOFF 1.0
#define HUGE_DISTANCE 10000.0
#define ELEC_DIST_CUTOFF 30.0
#define ELEC_DIST_CUTOFF2 ELEC_DIST_CUTOFF*ELEC_DIST_CUTOFF
#define VDW_DIST_CUTOFF 10.0
#define VDW_DIST_CUTOFF2 VDW_DIST_CUTOFF*VDW_DIST_CUTOFF


/**
 *
 * calculate_energy pyDock C implementation
 *
 **/
static PyObject * cdna_calculate_energy(PyObject *self, PyObject *args) {
    PyObject *receptor_coordinates, *ligand_coordinates = NULL;
    PyObject *tmp0, *tmp1 = NULL;
    PyArrayObject *rec_charges, *lig_charges, *rec_vdw, *lig_vdw, *rec_vdw_radii, *lig_vdw_radii = NULL;
    double atom_elec, total_elec, total_vdw, vdw_energy, vdw_radius, p6, k;
    unsigned int rec_len, lig_len, i, j;
    double **rec_array, **lig_array, x, y, z, distance2;
    npy_intp dims[2];
    PyArray_Descr *descr;
    double *rec_c_charges, *lig_c_charges, *rec_c_vdw, *lig_c_vdw, *rec_c_vdw_radii, *lig_c_vdw_radii = NULL;
    PyObject *result = PyTuple_New(2);

    total_elec = 0.0;
    atom_elec = 0.0;
    total_vdw = 0.0;

    if (PyArg_ParseTuple(args, "OOOOOOOO",
            &receptor_coordinates, &ligand_coordinates, &rec_charges, &lig_charges,
            &rec_vdw, &lig_vdw, &rec_vdw_radii, &lig_vdw_radii)) {

        descr = PyArray_DescrFromType(NPY_DOUBLE);

        tmp0 = PyObject_GetAttrString(receptor_coordinates, "coordinates");
        tmp1 = PyObject_GetAttrString(ligand_coordinates, "coordinates");

        rec_len = PySequence_Size(tmp0);
        lig_len = PySequence_Size(tmp1);

        dims[1] = 3;
        dims[0] = rec_len;
        PyArray_AsCArray((PyObject **)&tmp0, (void **)&rec_array, dims, 2, descr);

        dims[0] = lig_len;
        PyArray_AsCArray((PyObject **)&tmp1, (void **)&lig_array, dims, 2, descr);

        // Get pointers to the Python array structures
        rec_c_charges = PyArray_GETPTR1(rec_charges, 0);
        lig_c_charges = PyArray_GETPTR1(lig_charges, 0);
        rec_c_vdw = PyArray_GETPTR1(rec_vdw, 0);
        lig_c_vdw = PyArray_GETPTR1(lig_vdw, 0);
        rec_c_vdw_radii = PyArray_GETPTR1(rec_vdw_radii, 0);
        lig_c_vdw_radii = PyArray_GETPTR1(lig_vdw_radii, 0);

        // For all atoms in receptor
        for (i = 0; i < rec_len; i++) {
            // For all atoms in ligand
            for (j = 0; j < lig_len; j++) {
                // Euclidean^2 distance
                x = rec_array[i][0] - lig_array[j][0];
                y = rec_array[i][1] - lig_array[j][1];
                z = rec_array[i][2] - lig_array[j][2];
                distance2 = x*x + y*y + z*z;

                // Electrostatics energy
                if (distance2 <= ELEC_DIST_CUTOFF2) {
                    atom_elec = (rec_c_charges[i] * lig_c_charges[j]) / distance2;
                    if (atom_elec >= (MAX_ES_CUTOFF*EPSILON/FACTOR)) atom_elec = MAX_ES_CUTOFF*EPSILON/FACTOR;
                    if (atom_elec <= (MIN_ES_CUTOFF*EPSILON/FACTOR)) atom_elec = MIN_ES_CUTOFF*EPSILON/FACTOR;
                    total_elec += atom_elec;
                }

                // Van der Waals energy
                if (distance2 <= VDW_DIST_CUTOFF2){
                    vdw_energy = sqrt(rec_c_vdw[i] * lig_c_vdw[j]);
                    vdw_radius = rec_c_vdw_radii[i] + lig_c_vdw_radii[j];
                    p6 = pow(vdw_radius, 6) / pow(distance2, 3);
                    k = vdw_energy * (p6*p6 - 2.0 * p6);
                    if (k > VDW_CUTOFF) k = VDW_CUTOFF;
                    total_vdw += k;
                }
            }
        }
        // Convert total electrostatics to Kcal/mol:
        //      - coordinates are in Ang
        //      - charges are in e (elementary charge units)
        total_elec = total_elec * FACTOR / EPSILON;

        // Free structures
        PyArray_Free(tmp0, rec_array);
        PyArray_Free(tmp1, lig_array);
    }

    // Return a tuple with the following values for calculated energies:
    PyTuple_SetItem(result, 0, PyFloat_FromDouble(total_elec));
    PyTuple_SetItem(result, 1, PyFloat_FromDouble(total_vdw));
    return result;
}


/**
 *
 * Module methods table
 *
 **/
static PyMethodDef module_methods[] = {
    {"calculate_energy", (PyCFunction)cdna_calculate_energy, METH_VARARGS, "pyDockDNA C implementation"},
    {NULL}
};


/**
 *
 * Initialization function
 *
 **/
PyMODINIT_FUNC initcdna(void) {

    Py_InitModule3("cdna", module_methods, "cdna object");
    import_array();
}
