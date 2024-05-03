#include "js_to_py.h"

#include "error.h"
#include "jsfunction.h"


static void free_js_props(JSContext *ctx, JSPropertyEnum *props, size_t len) {
    if (!props)
        return;

    for (size_t i = 0; i < len; ++i)
        JS_FreeAtom(ctx, props[i].atom);

    js_free(ctx, props);
}


static ssize_t get_js_arr_length(JSContext *ctx, JSValueConst arr) {
    uint64_t length;
    JSValue val = JS_GetPropertyStr(ctx, arr, "length");
    int err = JS_ToIndex(ctx, &length, val);
    JS_FreeValue(ctx, val);
    return (err < 0 ? -1 : length);
}


static PyObject *js_str_to_py_obj(JSContext *ctx, JSValueConst val) {
    const char *val_str = JS_ToCString(ctx, val);
    PyObject *obj = PyUnicode_FromString(val_str);
    JS_FreeCString(ctx, val_str);
    return obj;
}


static PyObject *js_arr_to_py_obj(JSContext *ctx, JSValueConst val) {
    ssize_t length = get_js_arr_length(ctx, val);
    if (length < 0) {
        PyErr_SetString(PyExc_Exception, "invalid array length");
        return NULL;
    }

    PyObject *obj = PyList_New(length);
    if (!obj)
        return NULL;

    for (size_t i = 0; i < length; ++i) {
        JSValue val_i = JS_GetPropertyUint32(ctx, val, i);
        PyObject *obj_i = js_val_to_py_obj(ctx, val_i);
        JS_FreeValue(ctx, val_i);

        if (!obj_i) {
            Py_DECREF(obj);
            return NULL;
        }

        PyList_SetItem(obj, i, obj_i);
    }

    return obj;
}


static PyObject *js_obj_to_py_obj(JSContext *ctx, JSValueConst val) {
    JSPropertyEnum *props;
    uint32_t props_len;
    int err = JS_GetOwnPropertyNames(ctx, &props, &props_len, val,
                                     JS_GPN_STRING_MASK | JS_GPN_ENUM_ONLY);
    if (err < 0) {
        free_js_props(ctx, props, props_len);
        PyErr_SetString(PyExc_Exception, "can't get object properties");
        return NULL;
    }

    PyObject *obj = PyDict_New();
    if (!obj) {
        free_js_props(ctx, props, props_len);
        return NULL;
    }

    for (size_t i = 0; i < props_len; ++i) {
        const char *key = JS_AtomToCString(ctx, props[i].atom);
        if (!key) {
            Py_DECREF(obj);
            free_js_props(ctx, props, props_len);
            PyErr_SetString(PyExc_Exception, "unsupported object key");
            return NULL;
        }

        JSValue val_i = JS_GetProperty(ctx, val, props[i].atom);
        PyObject *obj_i = js_val_to_py_obj(ctx, val_i);
        JS_FreeValue(ctx, val_i);
        if (!obj_i) {
            JS_FreeCString(ctx, key);
            Py_DECREF(obj);
            free_js_props(ctx, props, props_len);
            return NULL;
        }

        int err = PyDict_SetItemString(obj, key, obj_i);
        JS_FreeCString(ctx, key);
        Py_DECREF(obj_i);
        if (err < 0) {
            Py_DECREF(obj);
            free_js_props(ctx, props, props_len);
            return NULL;
        }
    }

    free_js_props(ctx, props, props_len);
    return obj;
}


PyObject *js_val_to_py_obj(JSContext *ctx, JSValueConst val) {
    if (JS_IsException(val))
        return py_raise_js_exc(ctx);

    if (JS_IsNull(val) || JS_IsUndefined(val)) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    if (JS_IsBool(val))
        return PyBool_FromLong(JS_VALUE_GET_BOOL(val));

    if (JS_VALUE_GET_TAG(val) == JS_TAG_INT)
        return PyLong_FromLong(JS_VALUE_GET_INT(val));

    if (JS_TAG_IS_FLOAT64(JS_VALUE_GET_TAG(val)))
        return PyFloat_FromDouble(JS_VALUE_GET_FLOAT64(val));

    if (JS_IsString(val))
        return js_str_to_py_obj(ctx, val);

    if (JS_IsFunction(ctx, val))
        return (PyObject *)create_jsfunction(ctx, val);

    if (JS_IsArray(ctx, val))
        return js_arr_to_py_obj(ctx, val);

    if (JS_IsObject(val))
        return js_obj_to_py_obj(ctx, val);

    PyErr_SetString(PyExc_Exception, "unsupported value type");
    return NULL;
}
