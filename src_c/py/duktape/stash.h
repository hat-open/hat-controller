#ifndef PY_DUKTAPE_STASH_H
#define PY_DUKTAPE_STASH_H

#include <Python.h>
#include <duktape.h>

#include "safe_call.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef duk_int_t stash_id_t;

typedef struct {
    stash_id_t id;
    void *ptr;
} stash_put_data_t;

typedef struct {
    stash_id_t id;
} stash_get_data_t;

typedef struct {
    stash_id_t id;
} stash_del_data_t;


// ( id value -- ) without data
duk_ret_t stash_put(safe_call_ctx_t *cctx);
// ( id -- value ) without data
duk_ret_t stash_get(safe_call_ctx_t *cctx);
// ( id -- ) without data
duk_ret_t stash_del(safe_call_ctx_t *cctx);

// ( -- ) with data
duk_ret_t stash_put_data(safe_call_ctx_t *cctx);
// ( -- value ) with data
duk_ret_t stash_get_data(safe_call_ctx_t *cctx);
// ( -- ) with data
duk_ret_t stash_del_data(safe_call_ctx_t *cctx);

#ifdef __cplusplus
}
#endif

#endif
