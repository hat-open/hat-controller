#include "js_to_py.h"

#include "jsfunction.h"


// ( null -- ) without data
static PyObject *pop_null(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    Py_INCREF(Py_None);
    PyObject *obj = safe_call_add(cctx, Py_None);
    duk_pop(ctx);

    return obj;
}


// ( bool -- ) without data
static PyObject *pop_boolean(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_bool_t val = duk_get_boolean(ctx, -1);
    PyObject *obj = safe_call_add(cctx, PyBool_FromLong(val));
    duk_pop(ctx);

    return obj;
}


// ( num -- ) without data
static PyObject *pop_number(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_double_t val = duk_get_number(ctx, -1);
    PyObject *obj = safe_call_add(cctx, PyFloat_FromDouble(val));
    duk_pop(ctx);

    return obj;
}


// ( str -- ) without data
static PyObject *pop_string(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    const char *val = duk_get_string(ctx, -1);
    PyObject *obj = safe_call_add(cctx, PyUnicode_FromString(val));
    duk_pop(ctx);

    return obj;
}


// ( arr -- ) without data
static PyObject *pop_array(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = safe_call_add(cctx, PyList_New(0));
    if (!obj) {
        duk_pop(ctx);
        return NULL;
    }

    duk_enum(ctx, -1, DUK_ENUM_ARRAY_INDICES_ONLY);
    duk_remove(ctx, -2);

    while (duk_next(ctx, -1, 1)) {
        duk_remove(ctx, -2);

        PyObject *obj_i = js_to_py(cctx);
        if (!obj_i) {
            duk_pop(ctx);
            return NULL;
        }

        if (PyList_Append(obj, obj_i) < 0) {
            duk_pop(ctx);
            return NULL;
        }
    }

    duk_pop(ctx);
    return obj;
}


// ( obj -- ) without data
static PyObject *pop_object(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = safe_call_add(cctx, PyDict_New());
    if (!obj) {
        duk_pop(ctx);
        return NULL;
    }

    duk_enum(ctx, -1, DUK_ENUM_OWN_PROPERTIES_ONLY);
    duk_remove(ctx, -2);

    while (duk_next(ctx, -1, 1)) {
        PyObject *obj_value = js_to_py(cctx);
        if (!obj_value) {
            duk_pop_2(ctx);
            return NULL;
        }

        PyObject *obj_key = js_to_py(cctx);
        if (!obj_value) {
            duk_pop(ctx);
            return NULL;
        }

        if (PyDict_SetItem(obj, obj_key, obj_value) < 0) {
            duk_pop(ctx);
            return NULL;
        }
    }

    duk_pop(ctx);
    return obj;
}


// ( any -- ) without data
PyObject *js_to_py(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    if (duk_is_null_or_undefined(ctx, -1))
        return pop_null(cctx);

    if (duk_is_boolean(ctx, -1))
        return pop_boolean(cctx);

    if (duk_is_number(ctx, -1))
        return pop_number(cctx);

    if (duk_is_string(ctx, -1))
        return pop_string(cctx);

    if (duk_is_array(ctx, -1))
        return pop_array(cctx);

    if (duk_is_function(ctx, -1))
        return (PyObject *)create_jsfunction(cctx);

    if (duk_is_object(ctx, -1))
        return pop_object(cctx);

    PyErr_SetString(PyExc_Exception, "unsupported value type");
    return NULL;
}
