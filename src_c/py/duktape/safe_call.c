#include "safe_call.h"


static void free_objs(PyObject **objs, size_t objs_len) {
    for (size_t i = 0; i < objs_len; ++i)
        Py_DECREF(objs[i]);

    PyMem_Free(objs);
}


static duk_ret_t unsafe_call_py(duk_context *ctx, void *udata) {
    safe_call_ctx_t *cctx = udata;

    PyObject *obj = ((safe_call_py_cb_t)cctx->cb)(cctx);
    duk_push_pointer(ctx, obj);

    Py_XINCREF(obj);
    return 1;
}


static duk_ret_t unsafe_call_js(duk_context *ctx, void *udata) {
    safe_call_ctx_t *cctx = udata;

    return ((safe_call_js_cb_t)cctx->cb)(cctx);
}


PyObject *safe_call_py(duk_context *ctx, safe_call_py_cb_t cb, void *data,
                       duk_idx_t nargs) {
    safe_call_ctx_t cctx = {.ctx = ctx,
                            .cb = cb,
                            .data = data,
                            .objs = NULL,
                            .objs_size = 0,
                            .objs_len = 0};

    duk_int_t err = duk_safe_call(ctx, unsafe_call_py, &cctx, nargs, 1);
    free_objs(cctx.objs, cctx.objs_len);
    if (err) {
        PyErr_SetString(PyExc_Exception, duk_safe_to_string(ctx, -1));
        duk_pop(ctx);
        return NULL;
    }

    PyObject *obj = duk_get_pointer(ctx, -1);
    duk_pop(ctx);
    return obj;
}


duk_int_t safe_call_js(duk_context *ctx, safe_call_js_cb_t cb, void *data,
                       duk_idx_t nargs) {
    safe_call_ctx_t cctx = {.ctx = ctx,
                            .cb = cb,
                            .data = data,
                            .objs = NULL,
                            .objs_size = 0,
                            .objs_len = 0};

    duk_int_t err = duk_safe_call(ctx, unsafe_call_js, &cctx, nargs, 1);
    free_objs(cctx.objs, cctx.objs_len);

    return err;
}


PyObject *safe_call_add(safe_call_ctx_t *cctx, PyObject *obj) {
    if (!obj)
        return NULL;

    while (cctx->objs_size <= cctx->objs_len) {
        size_t objs_size = cctx->objs_size + 1024;
        PyObject **objs =
            PyMem_Realloc(cctx->objs, objs_size * sizeof(PyObject *));
        if (!objs) {
            Py_DECREF(obj);
            return NULL;
        }

        cctx->objs = objs;
        cctx->objs_size = objs_size;
    }

    cctx->objs[(cctx->objs_len)++] = obj;

    return obj;
}
