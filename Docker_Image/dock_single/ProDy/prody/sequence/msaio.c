#include "Python.h"
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "numpy/arrayobject.h"
#define LENLABEL 100
#define FASTALINELEN 1000
#define SELEXLINELEN 10000

static char *intcat(char *msg, int line) {

    /* Concatenate integer to a string. */

    char lnum[10];
    snprintf(lnum, 10, "%i", line);
    strcat(msg, lnum);
    return msg;
}


static int parseLabel(PyObject *labels, PyObject *mapping, char *line,
                      int length) {

    /* Append label to *labels*, extract identifier, and index label
       position in the list. Return 1 when successful, 0 on failure. */

    int i, ch, slash = 0, dash = 0;//, ipipe = 0, pipes[4] = {0, 0, 0, 0};

    for (i = 0; i < length; i++) {
        ch = line[i];
        if (ch < 32 && ch != 20)
            break;
        else if (ch == '/' && slash == 0 && dash == 0)
            slash = i;
        else if (ch == '-' && slash > 0 && dash == 0)
            dash = i;
        //else if (line[i] == '|' && ipipe < 4)
        //    pipes[ipipe++] = i;
    }

    PyObject *label, *index;
    #if PY_MAJOR_VERSION >= 3
    label = PyUnicode_FromStringAndSize(line, i);
    index = PyLong_FromSsize_t(PyList_Size(labels));
    #else
    label = PyString_FromStringAndSize(line, i);
    index = PyInt_FromSsize_t(PyList_Size(labels));
    #endif

    if (!label || !index || PyList_Append(labels, label) < 0) {
        PyObject *none = Py_None;
        PyList_Append(labels, none);
        Py_DECREF(none);

        Py_XDECREF(index);
        Py_XDECREF(label);
        return 0;
    }

    if (slash > 0 && dash > slash) {
        Py_DECREF(label);
        #if PY_MAJOR_VERSION >= 3
        label = PyUnicode_FromStringAndSize(line, slash);
        #else
        label = PyString_FromStringAndSize(line, slash);
        #endif
    }

    if (PyDict_Contains(mapping, label)) {
        PyObject *item = PyDict_GetItem(mapping, label); /* borrowed */
        if (PyList_Check(item)) {
            PyList_Append(item, index);
            Py_DECREF(index);
        } else {
            PyObject *list = PyList_New(2); /* new reference */
            PyList_SetItem(list, 0, item);
            Py_INCREF(item);
            PyList_SetItem(list, 1, index); /* steals reference, no DECREF */
            PyDict_SetItem(mapping, label, list);
            Py_DECREF(list);
        }
    } else {
        PyDict_SetItem(mapping, label, index);
        Py_DECREF(index);
    }

    Py_DECREF(label);
    return 1;
}


static PyObject *parseFasta(PyObject *self, PyObject *args) {

    /* Parse sequences from *filename* into the memory pointed by the
       Numpy array passed as Python object. */

    char *filename;
    PyArrayObject *msa;

    if (!PyArg_ParseTuple(args, "sO", &filename, &msa))
        return NULL;

    PyObject *labels = PyList_New(0), *mapping = PyDict_New();
    if (!labels || !mapping)
        return PyErr_NoMemory();

    char *line = malloc((FASTALINELEN) * sizeof(char));
    if (!line)
        return PyErr_NoMemory();

    char *data = (char *) PyArray_DATA(msa);

    int aligned = 1;
    char ch, errmsg[LENLABEL] = "failed to parse FASTA file at line ";
    long index = 0, count = 0;
    long iline = 0, i, seqlen = 0, curlen = 0;

    FILE *file = fopen(filename, "rb");
    while (fgets(line, FASTALINELEN, file) != NULL) {
        iline++;
        if (line[0] == '>') {
            if (seqlen != curlen) {
                if (seqlen) {
                    aligned = 0;
                    free(line);
                    free(data);
                    fclose(file);
                    PyErr_SetString(PyExc_IOError, intcat(errmsg, iline));
                    return NULL;
                } else
                    seqlen = curlen;
            }
            // `line + 1` is to omit `>` character
            count += parseLabel(labels, mapping, line + 1, FASTALINELEN);
            curlen = 0;
        } else {
            for (i = 0; i < FASTALINELEN; i++) {
                ch = line[i];
                if (ch < 32)
                    break;
                else {
                    data[index++] = ch;
                    curlen++;
                }
            }
        }
    }
    fclose(file);

    free(line);
    if (aligned && seqlen != curlen) {
        PyErr_SetString(PyExc_IOError, intcat(errmsg, iline));
        return NULL;
    }

    npy_intp dims[2] = {index / seqlen, seqlen};
    PyArray_Dims arr_dims;
    arr_dims.ptr = dims;
    arr_dims.len = 2;
    PyArray_Resize(msa, &arr_dims, 0, NPY_CORDER);
    PyObject *result = Py_BuildValue("(OOOi)", msa, labels, mapping, count);
    Py_DECREF(labels);
    Py_DECREF(mapping);
    return result;
}


static PyObject *writeFasta(PyObject *self, PyObject *args, PyObject *kwargs) {

    /* Write MSA where inputs are: labels in the form of Python lists
    and sequences in the form of Python numpy array and write them in
    FASTA format in the specified filename.*/

    char *filename;
    int line_length = 60;
    PyObject *labels;
    PyArrayObject *msa;

    static char *kwlist[] = {"filename", "labels", "msa", "line_length", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "sOO|i", kwlist,
                                     &filename, &labels, &msa, &line_length))
        return NULL;

    /* make sure to have a contiguous and well-behaved array */
    msa = PyArray_GETCONTIGUOUS(msa);

    long numseq = PyArray_DIMS(msa)[0], lenseq = PyArray_DIMS(msa)[1];

    if (numseq != PyList_Size(labels)) {
        PyErr_SetString(PyExc_ValueError,
            "size of labels and msa array does not match");
        return NULL;
    }

    FILE *file = fopen(filename, "wb");

    int nlines = lenseq / line_length;
    int remainder = lenseq - line_length * nlines;
    int i, j, k;
    int count = 0;
    char *seq = PyArray_DATA(msa);
    int lenmsa = strlen(seq);
    #if PY_MAJOR_VERSION >= 3
    PyObject *plabel;
    #endif
    for (i = 0; i < numseq; i++) {
        #if PY_MAJOR_VERSION >= 3
        plabel = PyUnicode_AsEncodedString(
                PyList_GetItem(labels, (Py_ssize_t) i), "utf-8",
                               "label encoding");
        char *label =  PyBytes_AsString(plabel);
        Py_DECREF(plabel);
        #else
        char *label =  PyString_AsString(PyList_GetItem(labels,
                                                        (Py_ssize_t) i));
        #endif
        fprintf(file, ">%s\n", label);

        for (j = 0; j < nlines; j++) {
            for (k = 0; k < 60; k++)
                if (count < lenmsa)
                    fprintf(file, "%c", seq[count++]);
            fprintf(file, "\n");
        }
        if (remainder)
            for (k = 0; k < remainder; k++)
                if (count < lenmsa)
                    fprintf(file, "%c", seq[count++]);

        fprintf(file, "\n");

    }
    fclose(file);
    return Py_BuildValue("s", filename);
}

static PyObject *parseSelex(PyObject *self, PyObject *args) {

    /* Parse sequences from *filename* into the the memory pointed by the
       Numpy array passed as Python object.  */

    char *filename;
    PyArrayObject *msa;

    if (!PyArg_ParseTuple(args, "sO", &filename, &msa))
        return NULL;

    long i = 0, beg = 0, end = 0;
    long size = SELEXLINELEN + 1, iline = 0, seqlen = 0;
    char errmsg[LENLABEL] = "failed to parse SELEX/Stockholm file at line ";

    PyObject *labels = PyList_New(0), *mapping = PyDict_New();
    if (!labels || !mapping)
        return PyErr_NoMemory();
    char *line = malloc(size * sizeof(char));
    if (!line)
        return PyErr_NoMemory();
    char *data = (char *) PyArray_DATA(msa);
    /* figure out where the sequence starts and ends in a line*/
    FILE *file = fopen(filename, "rb");
    while (fgets(line, size, file) != NULL) {
        iline++;
        if (line[0] == '#' || line[0] == '/' || line[0] == '%')
            continue;
        for (i = 0; i < size; i++)
            if (line[i] == ' ')
                break;
        for (; i < size; i++)
            if (line[i] != ' ')
                break;
        beg = i;
        for (; i < size; i++)
            if (line[i] < 32)
                break;
        end = i;
        seqlen = end - beg;
        break;
    }
    iline--;
    fseek(file, - strlen(line), SEEK_CUR);

    long index = 0, count = 0;

    int space = beg - 1; /* index of space character before sequence */
    while (fgets(line, size, file) != NULL) {
        iline++;
        if (line[0] == '#' || line[0] == '/' || line[0] == '%')
            continue;

        if (line[space] != ' ') {
            free(line);
            fclose(file);
            PyErr_SetString(PyExc_IOError, intcat(errmsg, iline));
            return NULL;
        }

        count += parseLabel(labels, mapping, line, space);

        for (i = beg; i < end; i++)
            data[index++] = line[i];
    }
    fclose(file);
    free(line);
    npy_intp dims[2] = {index / seqlen, seqlen};
    PyArray_Dims arr_dims;
    arr_dims.ptr = dims;
    arr_dims.len = 2;
    PyArray_Resize(msa, &arr_dims, 0, NPY_CORDER);
    PyObject *result = Py_BuildValue("(OOOi)", msa, labels, mapping, count);
    Py_DECREF(labels);
    Py_DECREF(mapping);

    return result;
}


static PyObject *writeSelex(PyObject *self, PyObject *args, PyObject *kwargs) {

    /* Write MSA where inputs are: labels in the form of Python lists
    and sequences in the form of Python numpy array and write them in
    SELEX (default) or Stockholm format in the specified filename.*/

    char *filename;
    PyObject *labels;
    PyArrayObject *msa;
    int stockholm;
    int label_length = 31;

    static char *kwlist[] = {"filename", "labels", "msa", "stockholm",
                             "label_length", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "sOO|ii", kwlist, &filename,
                                     &labels, &msa, &stockholm, &label_length))
        return NULL;

    /* make sure to have a contiguous and well-behaved array */
    msa = PyArray_GETCONTIGUOUS(msa);

    long numseq = PyArray_DIMS(msa)[0], lenseq = PyArray_DIMS(msa)[1];

    if (numseq != PyList_Size(labels)) {
        PyErr_SetString(PyExc_ValueError,
                        "size of labels and msa array does not match");
        return NULL;
    }

    FILE *file = fopen(filename, "wb");

    int i, j;
    int pos = 0;
    char *seq = PyArray_DATA(msa);
    if (stockholm)
        fprintf(file, "# STOCKHOLM 1.0\n");

    char *outline = (char *) malloc((label_length + lenseq + 2) *
                                    sizeof(char));

    outline[label_length + lenseq] = '\n';
    outline[label_length + lenseq + 1] = '\0';

    #if PY_MAJOR_VERSION >= 3
    PyObject *plabel;
    #endif
    for (i = 0; i < numseq; i++) {
        #if PY_MAJOR_VERSION >= 3
        plabel = PyUnicode_AsEncodedString(
                PyList_GetItem(labels, (Py_ssize_t) i), "utf-8",
                               "label encoding");
        char *label =  PyBytes_AsString(plabel);
        Py_DECREF(plabel);
        #else
        char *label = PyString_AsString(PyList_GetItem(labels, (Py_ssize_t)i));
        #endif
        int labelbuffer = label_length - strlen(label);

        strcpy(outline, label);

        if (labelbuffer > 0)
            for(j = strlen(label); j < label_length; j++)
                outline[j] = ' ';

        for (j = label_length; j < (lenseq + label_length); j++)
            outline[j] = seq[pos++];

        fprintf(file, "%s", outline);
    }

    if (stockholm)
        fprintf(file, "//\n");

    free(outline);
    fclose(file);
    return Py_BuildValue("s", filename);
}


static PyMethodDef msaio_methods[] = {

    {"parseFasta",  (PyCFunction)parseFasta, METH_VARARGS,
     "Return list of labels and a dictionary mapping labels to sequences \n"
     "after parsing the sequences into empty numpy character array."},

    {"writeFasta",  (PyCFunction)writeFasta, METH_VARARGS | METH_KEYWORDS,
     "Return filename after writing MSA in FASTA format."},

    {"parseSelex",  (PyCFunction)parseSelex, METH_VARARGS,
     "Return list of labels and a dictionary mapping labels to sequences \n"
     "after parsing the sequences into empty numpy character array."},

    {"writeSelex",  (PyCFunction)writeSelex, METH_VARARGS | METH_KEYWORDS,
    "Return filename after writing MSA in SELEX or Stockholm format."},

    {NULL, NULL, 0, NULL}
};


#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef msaiomodule = {
        PyModuleDef_HEAD_INIT,
        "msaio",
        "Multiple sequence alignment IO tools.",
        -1,
        msaio_methods
};
PyMODINIT_FUNC PyInit_msaio(void) {
    import_array();
    return PyModule_Create(&msaiomodule);
}
#else
PyMODINIT_FUNC initmsaio(void) {

    (void) Py_InitModule3("msaio", msaio_methods,
                          "Multiple sequence alignment IO tools.");

    import_array();
}
#endif


