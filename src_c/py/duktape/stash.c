#include "stash.h"


// ( id value -- ) without data
duk_ret_t stash_put(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_push_heap_stash(ctx);
    duk_insert(ctx, -3);
    duk_put_prop(ctx, -3);
    duk_pop(ctx);

    return 0;
}


// ( id -- value ) without data
duk_ret_t stash_get(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_push_heap_stash(ctx);
    duk_insert(ctx, -2);
    duk_get_prop(ctx, -2);
    duk_remove(ctx, -2);

    return 1;
}


// ( id -- ) without data
duk_ret_t stash_del(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;

    duk_push_heap_stash(ctx);
    duk_insert(ctx, -2);
    duk_del_prop(ctx, -2);
    duk_pop(ctx);

    return 0;
}


// ( -- ) with data
duk_ret_t stash_put_data(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;
    stash_put_data_t *data = cctx->data;

    duk_push_int(ctx, data->id);
    duk_push_pointer(ctx, data->ptr);

    return stash_put(cctx);
}


// ( -- value ) with data
duk_ret_t stash_get_data(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;
    stash_get_data_t *data = cctx->data;

    duk_push_int(ctx, data->id);

    return stash_get(cctx);
}


// ( -- ) with data
duk_ret_t stash_del_data(safe_call_ctx_t *cctx) {
    duk_context *ctx = cctx->ctx;
    stash_del_data_t *data = cctx->data;

    duk_push_int(ctx, data->id);

    return stash_del(cctx);
}
