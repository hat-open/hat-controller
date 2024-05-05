set breakpoint pending on

# break src_c/py/duktape/jsfunction.c:JsFunction_call
# break src_c/py/duktape/pyfunction.c:fn_call

# break src_c/py/quickjs/pyfunction.c:PyFunction_call
# break src_c/py/quickjs/pyfunction.c:create_pyfunction

# break src_c/py/lua/interpreter.c:Interpreter_dealloc
# break src_c/py/lua/luafunction.c:LuaFunction_dealloc
# break src_c/py/lua/pyobject.c:pyobject_gc
# break src_c/py/lua/lua_to_py.c:lua_table_to_py
# break src_c/py/lua/py_to_lua.c:py_dict_to_lua

run
