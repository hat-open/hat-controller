set breakpoint pending on

# break src_c/py/duktape/jsfunction.c:JsFunction_call
# break src_c/py/duktape/pyfunction.c:fn_call
break src_c/py/quickjs/pyfunction.c:PyFunction_call
break src_c/py/quickjs/pyfunction.c:create_pyfunction

run
