#include "quickjs.h"


JSValue js_throw_py_err(JSContext *ctx, const char *alternative) {
    PyObject *ptype;
    PyObject *pvalue;
    PyObject *ptraceback;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);

    Py_XDECREF(ptype);
    Py_XDECREF(ptraceback);

    if (!pvalue)
        return JS_Throw(ctx, JS_NewString(ctx, alternative));

    PyObject *py_str = PyObject_Str(pvalue);
    Py_DECREF(pvalue);
    if (!py_str)
        return JS_Throw(ctx, JS_NewString(ctx, alternative));

    const char *v = PyUnicode_AsUTF8AndSize(py_str, NULL);
    JSValue js_str = JS_NewString(ctx, (v ? v : alternative));

    Py_DECREF(py_str);

    return JS_Throw(ctx, js_str);
}


PyObject *py_raise_js_exc(JSContext *ctx) {
    JSValue exc = JS_GetException(ctx);
    const char *exc_str = JS_ToCString(ctx, exc);

    PyErr_SetString(PyExc_Exception, exc_str);

    JS_FreeCString(ctx, exc_str);
    JS_FreeValue(ctx, exc);

    return NULL;
}
