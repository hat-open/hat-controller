#include "luafunction.h"

#include <lauxlib.h>

#include "error.h"
#include "lua_to_py.h"
#include "py_to_lua.h"
#include "pyobject.h"
#include "util.h"


static PyObject *LuaFunction_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds) {
    LuaFunction *self = (LuaFunction *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->inter = NULL;
    self->ref = LUA_NOREF;

    return (PyObject *)self;
}


static void LuaFunction_dealloc(LuaFunction *self) {
    if (self->inter) {
        luaL_unref(self->inter->L, LUA_REGISTRYINDEX, self->ref);
        Py_DECREF(self->inter);
    }

    PyTypeObject *tp = Py_TYPE(self);
    PyObject_Free(self);
    Py_DECREF(tp);
}


static PyObject *LuaFunction_call(LuaFunction *self, PyObject *args,
                                  PyObject *kwargs) {
    if (!self->inter || self->ref == LUA_NOREF) {
        PyErr_SetString(PyExc_Exception, "function not initialized");
        return NULL;
    }

    lua_State *L = self->inter->L;
    PyObject *result = NULL;

    Py_ssize_t args_size = PyTuple_Size(args);
    if (args_size < 0) {
        PyErr_SetString(PyExc_Exception, "invalid args length");
        goto done;
    }

    lua_rawgeti(L, LUA_REGISTRYINDEX, self->ref);

    for (size_t i = 0; i < args_size; ++i) {
        PyObject *obj = PyTuple_GetItem(args, i);
        if (!obj) {
            PyErr_SetString(PyExc_Exception, "invalid args item");
            goto done;
        }

        lua_pushcfunction(L, py_to_lua);
        lua_pushlightuserdata(L, obj);
        if (lua_pcall(L, 1, 1, 0)) {
            py_raise_lua_error(L);
            goto done;
        }
    }

    PyThreadState *state = PyEval_SaveThread();

    int err = lua_pcall(L, args_size, 1, 0);

    PyEval_RestoreThread(state);

    if (err) {
        py_raise_lua_error(L);
        goto done;
    }

    lua_pushcfunction(L, lua_to_py);
    lua_insert(L, -2);
    err = lua_pcall(L, 1, 1, 0);
    if (err) {
        py_raise_lua_error(L);
        goto done;
    }

    result = get_pyobject(L, -1);
    if (!result)
        PyErr_SetString(PyExc_Exception, "invalid pyobject");

    Py_INCREF(result);

done:

    clear_lua_stack(L);

    return result;
}


static PyType_Slot luafunction_type_slots[] = {
    {Py_tp_new, LuaFunction_new},
    {Py_tp_dealloc, LuaFunction_dealloc},
    {Py_tp_call, LuaFunction_call},
    {0, NULL}};


static PyType_Spec luafunction_type_spec = {
    .name = "hat.controller.interpreters._lua.LuaFunction",
    .basicsize = sizeof(LuaFunction),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = luafunction_type_slots};


PyObject *create_luafunction_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &luafunction_type_spec, NULL);
}


// [-1, +1, e]
int create_luafunction(lua_State *L) {
    Interpreter *inter = get_interpreter(L);
    if (!inter)
        return luaL_error(L, "interpreter initialization error");

    new_pyobject(L);
    lua_insert(L, -2);

    LuaFunction *obj =
        (LuaFunction *)PyObject_CallNoArgs(inter->luafunction_type);
    set_pyobject(L, -2, (PyObject *)obj);
    if (!obj) {
        lua_pop(L, 1);
        return 1;
    }

    Py_INCREF(inter);
    obj->inter = inter;
    obj->ref = luaL_ref(L, LUA_REGISTRYINDEX);

    return 1;
}
