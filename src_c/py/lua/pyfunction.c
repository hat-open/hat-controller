#include "pyfunction.h"

#include <lauxlib.h>

#include "pyobject.h"
#include "error.h"
#include "lua_to_py.h"
#include "py_to_lua.h"


static int unsafe_pyfunction_call(lua_State *L) {
    PyObject *fn = lua_touserdata(L, 1);

    size_t args_len = lua_gettop(L) - 1;

    new_pyobject(L);
    lua_insert(L, 1);

    PyObject *args = PyTuple_New(args_len);
    set_pyobject(L, 1, args);
    if (!args)
        return lua_raise_py_error(L, "error creating tuple");

    for (ssize_t i = args_len - 1; i >= 0; --i) {
        lua_to_py(L);

        PyObject *arg = get_pyobject(L, -1);
        if (!args)
            return lua_raise_py_error(L, "error converting argument");

        Py_INCREF(arg);
        if (PyTuple_SetItem(args, i, args) < 0)
            return lua_raise_py_error(L, "error setting argument");

        lua_pop(L, 1);
    }

    new_pyobject(L);
    lua_insert(L, 1);

    PyObject *obj = PyObject_Call(fn, args, NULL);
    set_pyobject(L, 1, obj);
    if (!obj)
        return lua_raise_py_error(L, "function call error");

    lua_settop(L, 1);

    lua_pushlightuserdata(L, obj);
    py_to_lua(L);

    lua_insert(L, 1);
    lua_settop(L, 1);

    return 1;
}


static int pyfunction_call(lua_State *L) {
    PyObject *fn = get_pyobject(L, lua_upvalueindex(1));
    if (!fn)
        return luaL_error(L, "invalid function");

    lua_pushlightuserdata(L, fn);
    lua_insert(L, 1);

    lua_pushcfunction(L, unsafe_pyfunction_call);
    lua_insert(L, 1);

    PyGILState_STATE state = PyGILState_Ensure();

    int err = lua_pcall(L, lua_gettop(L) - 1, 1, 0);

    PyGILState_Release(state);

    if (err)
        return lua_error(L);

    return 1;
}


// [-0, +1, e]
int create_pyfunction(lua_State *L, PyObject *fn) {
    new_pyobject(L);
    Py_INCREF(fn);
    set_pyobject(L, -1, fn);

    lua_pushcclosure(L, pyfunction_call, 1);
    return 1;
}
