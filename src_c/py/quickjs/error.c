#include "quickjs.h"


JSValue js_throw_py_err(JSContext *ctx, const char *alternative) {
    PyObject *ptype;
    PyObject *pvalue;
    PyObject *ptraceback;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);

    PyObject *ptype_str = NULL;
    PyObject *pvalue_str = NULL;

    JSValue err;

    if (!ptype || !pvalue) {
        err = JS_ThrowInternalError(ctx, "%s", alternative);
        goto done;
    }

    ptype_str = PyObject_GetAttrString(ptype, "__name__");
    pvalue_str = PyObject_Str(pvalue);

    if (!ptype_str || !pvalue_str) {
        err = JS_ThrowInternalError(ctx, "%s", alternative);
        goto done;
    }

    const char *type = PyUnicode_AsUTF8AndSize(ptype_str, NULL);
    const char *value = PyUnicode_AsUTF8AndSize(pvalue_str, NULL);

    if (!type || !value) {
        err = JS_ThrowInternalError(ctx, "%s", alternative);
        goto done;
    }

    err = JS_ThrowInternalError(ctx, "%s: %s", type, value);

done:

    Py_XDECREF(ptype);
    Py_XDECREF(pvalue);
    Py_XDECREF(ptraceback);

    Py_XDECREF(ptype_str);
    Py_XDECREF(pvalue_str);

    return err;
}


PyObject *py_raise_js_exc(JSContext *ctx) {
    JSValue exc = JS_GetException(ctx);

    if (!JS_IsError(ctx, exc)) {
        const char *exc_str = JS_ToCString(ctx, exc);
        JS_FreeValue(ctx, exc);

        PyErr_SetString(PyExc_Exception, exc_str);
        JS_FreeCString(ctx, exc_str);

        return NULL;
    }

    JSValue name = JS_GetPropertyStr(ctx, exc, "name");
    const char *name_str = JS_ToCString(ctx, name);
    JS_FreeValue(ctx, name);

    JSValue message = JS_GetPropertyStr(ctx, exc, "message");
    const char *message_str = JS_ToCString(ctx, message);
    JS_FreeValue(ctx, message);

    JSValue stack = JS_GetPropertyStr(ctx, exc, "stack");
    const char *stack_str = JS_ToCString(ctx, stack);
    JS_FreeValue(ctx, stack);

    JS_FreeValue(ctx, exc);

    PyErr_Format(PyExc_Exception, "%s: %s\n%s", (name_str ? name_str : "error"),
                 (message_str ? message_str : ""),
                 (stack_str ? stack_str : ""));

    if (name_str)
        JS_FreeCString(ctx, name_str);

    if (message_str)
        JS_FreeCString(ctx, message_str);

    if (stack_str)
        JS_FreeCString(ctx, stack_str);

    return NULL;
}
