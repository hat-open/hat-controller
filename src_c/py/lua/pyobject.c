#include "pyobject.h"

#include <lauxlib.h>


static int pyobject_meta_key;


static int pyobject_gc(lua_State *L) {
    PyObject **p = lua_touserdata(L, -1);
    if (!p || !(*p))
        return 0;

    PyGILState_STATE state = PyGILState_Ensure();
    Py_DECREF(*p);
    PyGILState_Release(state);

    return 0;
}


// [-0, +0, e]
int init_pyobject(lua_State *L) {
    lua_newtable(L);

    lua_pushstring(L, "__gc");
    lua_pushcfunction(L, pyobject_gc);
    lua_rawset(L, -3);

    lua_rawsetp(L, LUA_REGISTRYINDEX, &pyobject_meta_key);

    return 0;
}


// [-0, +1, e]
void new_pyobject(lua_State *L) {
    PyObject **p = lua_newuserdatauv(L, sizeof(PyObject *), 0);
    *p = NULL;

    lua_rawgetp(L, LUA_REGISTRYINDEX, &pyobject_meta_key);

    lua_setmetatable(L, -2);
}


// [-0, +0, -] - steals obj ref
int set_pyobject(lua_State *L, int index, PyObject *obj) {
    PyObject **p = lua_touserdata(L, index);
    if (!p) {
        Py_XDECREF(obj);
        return -1;
    }

    Py_XDECREF(*p);
    *p = obj;

    return 0;
}


// [-0, +0, -] - returns borrowed ref
PyObject *get_pyobject(lua_State *L, int index) {
    PyObject **p = lua_touserdata(L, index);
    if (!p)
        return NULL;

    return *p;
}
