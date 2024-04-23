#ifndef PY_DUKTAPE_SAFE_CALL_H
#define PY_DUKTAPE_SAFE_CALL_H

#include <Python.h>
#include <duktape.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    duk_context *ctx;
    void *cb;
    void *data;
    PyObject **objs;
    size_t objs_size;
    size_t objs_len;
} safe_call_ctx_t;

typedef PyObject *(*safe_call_py_cb_t)(safe_call_ctx_t *cctx);
typedef duk_ret_t (*safe_call_js_cb_t)(safe_call_ctx_t *cctx);


// ( any_1 ... any_n -- )
PyObject *safe_call_py(duk_context *ctx, safe_call_py_cb_t cb, void *data,
                       duk_idx_t nargs);
// ( any_1 ... any_n -- any )
duk_int_t safe_call_js(duk_context *ctx, safe_call_js_cb_t cb, void *data,
                       duk_idx_t nargs);

// steals obj reference
PyObject *safe_call_add(safe_call_ctx_t *cctx, PyObject *obj);

#ifdef __cplusplus
}
#endif

#endif
