#include "quickjs.h"


static JSValue get_function_proto(JSContext *ctx) {
    // TODO there should be better way to obtain function prototype

    JSValue fn = JS_NewCFunction(ctx, NULL, "", 0);
    if (JS_IsException(fn))
        return fn;

    JSValue proto = JS_GetPrototype(ctx, fn);
    JS_FreeValue(ctx, fn);

    return proto;
}


static void PyFunction_finalizer(JSRuntime *rt, JSValue val) {
    Interpreter *inter = JS_GetRuntimeOpaque(rt);
    if (!inter)
        return;

    PyObject *fn = JS_GetOpaque(val, inter->pyfunction_cid);
    if (!fn)
        return;

    PyGILState_STATE state = PyGILState_Ensure();
    Py_DECREF(fn);
    PyGILState_Release(state);
}


static JSValue PyFunction_call(JSContext *ctx, JSValueConst func_obj,
                               JSValueConst this_val, int argc,
                               JSValueConst *argv, int flags) {
    Interpreter *inter = JS_GetContextOpaque(ctx);
    if (!inter)
        return JS_Throw(ctx,
                        JS_NewString(ctx, "interpreter initialization error"));

    PyObject *fn = JS_GetOpaque(func_obj, inter->pyfunction_cid);
    if (!fn)
        return JS_Throw(ctx,
                        JS_NewString(ctx, "function initialization error"));

    JSValue val = JS_UNINITIALIZED;
    PyObject *py_args = NULL;
    PyObject *py_obj = NULL;

    PyGILState_STATE state = PyGILState_Ensure();

    py_args = PyTuple_New(argc);
    if (!py_args) {
        val = js_throw_py_err(ctx, "error creating tuple");
        goto done;
    }

    for (size_t i = 0; i < argc; ++i) {
        PyObject *py_arg = js_val_to_py_obj(ctx, argv[i]);
        if (!py_arg) {
            val = js_throw_py_err(ctx, "error converting argument");
            goto done;
        }

        if (PyTuple_SetItem(py_args, i, py_arg) < 0) {
            val = js_throw_py_err(ctx, "error setting argument");
            goto done;
        }
    }

    py_obj = PyObject_Call(fn, py_args, NULL);
    if (!py_obj) {
        val = js_throw_py_err(ctx, "function call error");
        goto done;
    }

    val = py_obj_to_js_val(ctx, py_obj);

done:

    Py_XDECREF(py_args);
    Py_XDECREF(py_obj);

    PyGILState_Release(state);
    return val;
}


static const JSClassDef PyFunction_def = {.class_name = "PyFunction",
                                          .finalizer = PyFunction_finalizer,
                                          .call = PyFunction_call};


JSClassID create_pyfunction_class(JSRuntime *rt) {
    JSClassID cid = JS_INVALID_CLASS_ID;
    if (JS_NewClassID(&cid) == JS_INVALID_CLASS_ID)
        return JS_INVALID_CLASS_ID;

    if (JS_NewClass(rt, cid, &PyFunction_def) < 0)
        return JS_INVALID_CLASS_ID;

    return cid;
}


JSValue create_pyfunction(JSContext *ctx, PyObject *fn) {
    Interpreter *inter = JS_GetContextOpaque(ctx);
    if (!inter)
        return JS_Throw(ctx,
                        JS_NewString(ctx, "interpreter initialization error"));

    JSValue proto = get_function_proto(ctx);
    if (JS_IsException(proto))
        return proto;

    JSValue val = JS_NewObjectProtoClass(ctx, proto, inter->pyfunction_cid);
    JS_FreeValue(ctx, proto);
    if (JS_IsException(val))
        return val;

    Py_INCREF(fn);
    JS_SetOpaque(val, fn);

    return val;
}
