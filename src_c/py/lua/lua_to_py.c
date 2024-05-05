#include "lua_to_py.h"

#include <lauxlib.h>

#include "luafunction.h"
#include "pyobject.h"


static int lua_nil_to_py(lua_State *L) {
    lua_pop(L, 1);

    new_pyobject(L);
    Py_INCREF(Py_None);
    set_pyobject(L, -1, Py_None);

    return 1;
}


static int lua_boolean_to_py(lua_State *L) {
    int val = lua_toboolean(L, -1);
    lua_pop(L, 1);

    new_pyobject(L);
    PyObject *obj = PyBool_FromLong(val);
    set_pyobject(L, -1, obj);

    return 1;
}


static int lua_integer_to_py(lua_State *L) {
    lua_Integer val = lua_tointeger(L, -1);
    lua_pop(L, 1);

    new_pyobject(L);
    PyObject *obj = PyLong_FromLong(val);
    set_pyobject(L, -1, obj);

    return 1;
}


static int lua_number_to_py(lua_State *L) {
    lua_Number val = lua_tonumber(L, -1);
    lua_pop(L, 1);

    new_pyobject(L);
    PyObject *obj = PyFloat_FromDouble(val);
    set_pyobject(L, -1, obj);

    return 1;
}


static int lua_string_to_py(lua_State *L) {
    size_t val_len;
    const char *val = lua_tolstring(L, -1, &val_len);

    new_pyobject(L);
    PyObject *obj = PyUnicode_FromStringAndSize(val, val_len);
    set_pyobject(L, -1, obj);

    lua_insert(L, -2);
    lua_pop(L, 1);

    return 1;
}


static int lua_sequence_to_py(lua_State *L) {
    new_pyobject(L);
    lua_insert(L, -2);

    PyObject *obj = PyList_New(0);
    set_pyobject(L, -2, obj);
    if (!obj) {
        lua_pop(L, 1);
        return 1;
    }

    for (size_t i = 0; lua_rawgeti(L, -1, i + 1) != LUA_TNIL; ++i) {
        lua_to_py(L);
        PyObject *val = get_pyobject(L, -1);
        if (!val) {
            lua_pop(L, 2);
            set_pyobject(L, -1, NULL);
            return 1;
        }

        if (PyList_Append(obj, val)) {
            lua_pop(L, 2);
            set_pyobject(L, -1, NULL);
            return 1;
        }

        lua_pop(L, 1);
    }

    lua_pop(L, 2);

    return 1;
}


static int lua_table_to_py(lua_State *L) {
    new_pyobject(L);
    lua_insert(L, -2);

    PyObject *obj = PyDict_New();
    set_pyobject(L, -2, obj);
    if (!obj) {
        lua_pop(L, 1);
        return 1;
    }

    lua_pushnil(L);
    while (lua_next(L, -2)) {
        if (!lua_isstring(L, -2))
            return luaL_error(L, "unsupported object key");

        const char *key = lua_tolstring(L, -2, NULL);
        if (!key)
            return luaL_error(L, "unsupported object key");

        lua_to_py(L);
        PyObject *val = get_pyobject(L, -1);
        if (!val) {
            lua_pop(L, 3);
            set_pyobject(L, -1, NULL);
            return 1;
        }

        if (PyDict_SetItemString(obj, key, val)) {
            lua_pop(L, 3);
            set_pyobject(L, -1, NULL);
            return 1;
        }

        lua_pop(L, 1);
    }

    lua_pop(L, 1);

    return 1;
}


// [-1, +1, e]
int lua_to_py(lua_State *L) {
    if (lua_isnil(L, -1))
        return lua_nil_to_py(L);

    if (lua_isboolean(L, -1))
        return lua_boolean_to_py(L);

    if (lua_isinteger(L, -1))
        return lua_integer_to_py(L);

    if (lua_isnumber(L, -1))
        return lua_number_to_py(L);

    if (lua_isstring(L, -1))
        return lua_string_to_py(L);

    if (lua_isfunction(L, -1))
        return create_luafunction(L);

    if (lua_istable(L, -1)) {
        int is_sequence = lua_rawgeti(L, -1, 1) != LUA_TNIL;
        lua_pop(L, 1);
        if (is_sequence)
            return lua_sequence_to_py(L);

        lua_pushnil(L);
        if (!lua_next(L, -2))
            return lua_sequence_to_py(L);
        lua_pop(L, 2);

        return lua_table_to_py(L);
    }

    return luaL_error(L, "invalid lua type");
}
