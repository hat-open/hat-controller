#include "py_to_lua.h"

#include <lauxlib.h>

#include "error.h"
#include "pyfunction.h"


static int py_int_to_lua(lua_State *L, PyObject *obj) {
    long v = PyLong_AsLong(obj);
    if (v == -1 && PyErr_Occurred())
        return lua_raise_py_error(L, "convert int error");

    lua_pushinteger(L, v);
    return 1;
}


static int py_float_to_lua(lua_State *L, PyObject *obj) {
    double v = PyFloat_AsDouble(obj);
    if (v == -1 && PyErr_Occurred())
        return lua_raise_py_error(L, "convert float error");

    lua_pushnumber(L, v);
    return 1;
}


static int py_str_to_lua(lua_State *L, PyObject *obj) {
    Py_ssize_t v_len;
    const char *v = PyUnicode_AsUTF8AndSize(obj, &v_len);
    if (!v)
        return lua_raise_py_error(L, "convert str error");

    lua_pushlstring(L, v, v_len);
    return 1;
}


static int py_list_to_lua(lua_State *L, PyObject *obj) {
    Py_ssize_t len = PyList_Size(obj);
    if (len < 0)
        return lua_raise_py_error(L, "invalid list size");

    lua_newtable(L);

    for (size_t i = 0; i < len; ++i) {
        PyObject *obj_i = PyList_GetItem(obj, i);
        if (!obj_i)
            return lua_raise_py_error(L, "get item error");

        lua_pushlightuserdata(L, obj_i);
        py_to_lua(L);

        lua_seti(L, -2, i + 1);
    }

    return 1;
}


static int py_dict_to_lua(lua_State *L, PyObject *obj) {
    lua_newtable(L);

    PyObject *obj_k, *obj_v;
    Py_ssize_t i = 0;

    while (PyDict_Next(obj, &i, &obj_k, &obj_v)) {
        Py_ssize_t key_len;
        const char *key = PyUnicode_AsUTF8AndSize(obj_k, &key_len);
        if (!key)
            return lua_raise_py_error(L, "invalid key");

        lua_pushlstring(L, key, key_len);

        lua_pushlightuserdata(L, obj_v);
        py_to_lua(L);

        lua_settable(L, -3);
    }

    return 1;
}


// [-1, +1, e]
int py_to_lua(lua_State *L) {
    PyObject *obj = lua_touserdata(L, -1);
    lua_pop(L, 1);

    if (obj == Py_None) {
        lua_pushnil(L);
        return 1;
    }

    if (PyBool_Check(obj)) {
        lua_pushboolean(L, PyObject_IsTrue(obj));
        return 1;
    }

    if (PyLong_Check(obj))
        return py_int_to_lua(L, obj);

    if (PyFloat_Check(obj))
        return py_float_to_lua(L, obj);

    if (PyUnicode_Check(obj))
        return py_str_to_lua(L, obj);

    if (PyCallable_Check(obj)) {
        return create_pyfunction(L, obj);
    }

    if (PyList_Check(obj))
        return py_list_to_lua(L, obj);

    if (PyDict_Check(obj))
        return py_dict_to_lua(L, obj);

    return luaL_error(L, "unsupported type");
}
