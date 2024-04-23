#include "pyfunction.h"

#include "js_to_py.h"
#include "py_to_js.h"


typedef struct {
    duk_errcode_t err;
    const char *msg;
} push_err_data_t;


// ( -- err ) with data
static duk_ret_t push_err_data(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;
    push_err_data_t *data = cctx->data;

    duk_push_error_object(ctx, data->err, data->msg);

    return 1;
}


static duk_ret_t push_py_exc(duk_context *ctx, const char *alternative) {
    PyObject *py_type;
    PyObject *py_value;
    PyObject *py_traceback;

    PyErr_Fetch(&py_type, &py_value, &py_traceback);

    Py_XDECREF(py_type);
    Py_XDECREF(py_traceback);

    if (!py_value) {
        push_err_data_t err_data = {.err = DUK_ERR_ERROR, .msg = alternative};
        return safe_call_js(ctx, push_err_data, &err_data, 0);
    }

    PyObject *py_str = PyObject_Str(py_value);
    Py_DECREF(py_value);
    if (!py_str) {
        push_err_data_t err_data = {.err = DUK_ERR_ERROR, .msg = alternative};
        return safe_call_js(ctx, push_err_data, &err_data, 0);
    }

    const char *str = PyUnicode_AsUTF8AndSize(py_str, NULL);

    push_err_data_t err_data = {.err = DUK_ERR_ERROR, .msg = str};
    duk_ret_t err = safe_call_js(ctx, push_err_data, &err_data, 0);

    Py_DECREF(py_str);

    return err;
}


static duk_ret_t fn_call(duk_context *ctx) {
    duk_idx_t nargs = duk_get_top(ctx);

    duk_push_current_function(ctx);
    duk_get_prop_literal(ctx, -1, "_fn_ptr");
    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop_2(ctx);
    if (!obj)
        return duk_error(ctx, DUK_ERR_ERROR, "function initialization error");

    PyObject *args = NULL;
    duk_int_t err = 0;
    PyObject *result = NULL;

    PyGILState_STATE state = PyGILState_Ensure();

    args = PyTuple_New(nargs);
    if (!args) {
        push_err_data_t err_data = {.err = DUK_ERR_ERROR,
                                    .msg = "error creating tuple"};
        safe_call_js(ctx, push_err_data, &err_data, 0);
        err = 1;
        goto done;
    }

    for (ssize_t i = nargs - 1; i >= 0; --i) {
        PyObject *arg = safe_call_py(ctx, js_to_py, NULL, 1);
        if (!arg) {
            push_py_exc(ctx, "error converting argument");
            err = 1;
            goto done;
        }

        if (PyTuple_SetItem(args, i, arg) < 0) {
            push_err_data_t err_data = {.err = DUK_ERR_ERROR,
                                        .msg = "error setting argument"};
            safe_call_js(ctx, push_err_data, &err_data, 0);
            err = 1;
            goto done;
        }
    }

    result = PyObject_Call(obj, args, NULL);
    if (!result) {
        push_py_exc(ctx, "error converting result");
        err = 1;
        goto done;
    }

    py_to_js_data_t data = {.obj = result};
    err = safe_call_js(ctx, py_to_js_data, &data, 0);

done:

    Py_XDECREF(result);
    Py_XDECREF(args);

    PyGILState_Release(state);

    if (err)
        return duk_throw(ctx);

    return 1;
}


static duk_ret_t fn_finalizer(duk_context *ctx) {
    duk_get_prop_literal(ctx, 0, "_fn_ptr");

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);
    if (!obj)
        return 0;

    PyGILState_STATE state = PyGILState_Ensure();
    Py_DECREF(obj);
    PyGILState_Release(state);

    return 0;
}


// ( ptr -- fn ) without data
duk_ret_t create_pyfunction(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);

    duk_push_c_function(ctx, fn_call, DUK_VARARGS);

    duk_push_pointer(ctx, obj);
    duk_put_prop_literal(ctx, -2, "_fn_ptr");

    duk_push_c_function(ctx, fn_finalizer, 1);
    duk_set_finalizer(ctx, -2);

    // TODO posible memory leak if error raised after Py_INCREF
    Py_INCREF(obj);

    return 1;
}
