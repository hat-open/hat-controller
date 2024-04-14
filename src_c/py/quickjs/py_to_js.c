#include "quickjs.h"


static JSValue py_int_to_js_val(JSContext *ctx, PyObject *obj) {
    long v = PyLong_AsLong(obj);
    if (v == -1 && PyErr_Occurred())
        return js_throw_py_err(ctx, "convert int error");

    return JS_NewInt64(ctx, v);
}


static JSValue py_float_to_js_val(JSContext *ctx, PyObject *obj) {
    double v = PyFloat_AsDouble(obj);
    if (v == -1 && PyErr_Occurred())
        return js_throw_py_err(ctx, "convert float error");

    return JS_NewFloat64(ctx, v);
}


static JSValue py_str_to_js_val(JSContext *ctx, PyObject *obj) {
    Py_ssize_t v_len;
    const char *v = PyUnicode_AsUTF8AndSize(obj, &v_len);
    if (!v)
        return js_throw_py_err(ctx, "convert str error");

    return JS_NewStringLen(ctx, v, v_len);
}


static JSValue py_list_to_js_val(JSContext *ctx, PyObject *obj) {
    Py_ssize_t len = PyList_Size(obj);
    if (len < 0)
        return js_throw_py_err(ctx, "invalid list size");

    JSValue val = JS_NewArray(ctx);
    if (JS_IsException(val))
        return val;

    for (size_t i = 0; i < len; ++i) {
        PyObject *obj_i = PyList_GetItem(obj, i);
        if (!obj_i) {
            JS_FreeValue(ctx, val);
            return js_throw_py_err(ctx, "get item error");
        }

        JSValue val_i = py_obj_to_js_val(ctx, obj_i);
        if (JS_IsException(val_i)) {
            JS_FreeValue(ctx, val);
            return val_i;
        }

        int err = JS_SetPropertyInt64(ctx, val, i, val_i);
        if (err < 0) {
            JS_FreeValue(ctx, val);
            return JS_Throw(ctx, JS_NewString(ctx, "error setting item"));
        }
    }

    return val;
}


static JSValue py_dict_to_js_val(JSContext *ctx, PyObject *obj) {
    JSValue val = JS_NewObject(ctx);
    if (JS_IsException(val))
        return val;

    PyObject *obj_k, *obj_v;
    Py_ssize_t i = 0;

    while (PyDict_Next(obj, &i, &obj_k, &obj_v)) {
        const char *key = PyUnicode_AsUTF8AndSize(obj_k, NULL);
        if (!key) {
            JS_FreeValue(ctx, val);
            return js_throw_py_err(ctx, "invalid key");
        }

        JSValue val_i = py_obj_to_js_val(ctx, obj_v);
        if (JS_IsException(val)) {
            JS_FreeValue(ctx, val);
            return val_i;
        }

        int err = JS_SetPropertyStr(ctx, val, key, val_i);
        if (err < 0) {
            JS_FreeValue(ctx, val);
            return JS_Throw(ctx, JS_NewString(ctx, "error setting item"));
        }
    }

    return val;
}


JSValue py_obj_to_js_val(JSContext *ctx, PyObject *obj) {
    if (obj == Py_None)
        return JS_NULL;

    if (PyBool_Check(obj))
        return (PyObject_IsTrue(obj) ? JS_TRUE : JS_FALSE);

    if (PyLong_Check(obj))
        return py_int_to_js_val(ctx, obj);

    if (PyFloat_Check(obj))
        return py_int_to_js_val(ctx, obj);

    if (PyUnicode_Check(obj))
        return py_str_to_js_val(ctx, obj);

    if (PyCallable_Check(obj))
        return create_pyfunction(ctx, obj);

    if (PyList_Check(obj))
        return py_list_to_js_val(ctx, obj);

    if (PyDict_Check(obj))
        return py_dict_to_js_val(ctx, obj);

    return JS_Throw(ctx, JS_NewString(ctx, "unsupported type"));
}
