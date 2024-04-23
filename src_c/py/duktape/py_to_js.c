#include "py_to_js.h"

#include "pyfunction.h"


// ( ptr -- null ) without data
static duk_ret_t push_null(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_pop(ctx);

    duk_push_null(ctx);
    return 1;
}


// ( ptr -- bool ) without data
static duk_ret_t push_bool(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    duk_push_boolean(ctx, PyObject_IsTrue(obj));
    return 1;
}


// ( ptr -- int ) without data
static duk_ret_t push_int(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    duk_push_int(ctx, PyLong_AsLong(obj));
    return 1;
}


// ( ptr -- num ) without data
static duk_ret_t push_num(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    duk_push_number(ctx, PyFloat_AsDouble(obj));
    return 1;
}


// ( ptr -- str ) without data
static duk_ret_t push_str(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    Py_ssize_t v_len;
    const char *v = PyUnicode_AsUTF8AndSize(obj, &v_len);

    duk_push_lstring(ctx, v, v_len);
    return 1;
}


// ( ptr -- arr ) without data
static duk_ret_t push_arr(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    Py_ssize_t len = PyList_Size(obj);
    if (len < 0)
        return duk_error(ctx, DUK_ERR_ERROR, "invalid list size");

    duk_push_array(ctx);

    for (size_t i = 0; i < len; ++i) {
        PyObject *obj_i = PyList_GetItem(obj, i);
        if (!obj_i)
            return duk_error(ctx, DUK_ERR_ERROR, "get item error");

        duk_push_pointer(ctx, obj_i);
        py_to_js(cctx);

        duk_put_prop_index(ctx, -2, i);
    }

    return 1;
}


// ( ptr -- obj ) without data
static duk_ret_t push_obj(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    duk_push_object(ctx);

    PyObject *obj_k, *obj_v;
    Py_ssize_t i = 0;

    while (PyDict_Next(obj, &i, &obj_k, &obj_v)) {
        duk_push_pointer(ctx, obj_k);
        py_to_js(cctx);

        duk_push_pointer(ctx, obj_v);
        py_to_js(cctx);

        duk_put_prop(ctx, -3);
    }

    return 1;
}


// ( ptr -- any ) without data
duk_ret_t py_to_js(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);

    if (obj == Py_None)
        return push_null(cctx);

    if (PyBool_Check(obj))
        return push_bool(cctx);

    if (PyLong_Check(obj))
        return push_int(cctx);

    if (PyFloat_Check(obj))
        return push_num(cctx);

    if (PyUnicode_Check(obj))
        return push_str(cctx);

    if (PyCallable_Check(obj))
        return create_pyfunction(cctx);

    if (PyList_Check(obj))
        return push_arr(cctx);

    if (PyDict_Check(obj))
        return push_obj(cctx);

    duk_pop(ctx);
    return duk_error(ctx, DUK_ERR_TYPE_ERROR, "unsupported type");
}


// ( -- any ) with data
duk_ret_t py_to_js_data(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;
    py_to_js_data_t *data = cctx->data;

    duk_push_pointer(ctx, data->obj);

    return py_to_js(cctx);
}
