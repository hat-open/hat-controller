#include "interpreter.h"

#include <lauxlib.h>
#include <lualib.h>

#include "error.h"
#include "module.h"
#include "lua_to_py.h"
#include "pyobject.h"
#include "util.h"


static int interpreter_key;


static const luaL_Reg libs[] = {{LUA_GNAME, luaopen_base},
                                {LUA_COLIBNAME, luaopen_coroutine},
                                {LUA_TABLIBNAME, luaopen_table},
                                {LUA_STRLIBNAME, luaopen_string},
                                {LUA_MATHLIBNAME, luaopen_math},
                                {LUA_UTF8LIBNAME, luaopen_utf8},
                                {NULL, NULL}};


static void *l_alloc(void *ud, void *ptr, size_t osize, size_t nsize) {
    if (nsize)
        return realloc(ptr, nsize);

    free(ptr);
    return NULL;
}


static int init_lua_state(lua_State *L) {
    lua_rawsetp(L, LUA_REGISTRYINDEX, &interpreter_key);

    for (const luaL_Reg *lib = libs; lib->func; lib++) {
        luaL_requiref(L, lib->name, lib->func, 1);
        lua_pop(L, 1);
    }

    init_pyobject(L);

    return 0;
}


static PyObject *Interpreter_new(PyTypeObject *type, PyObject *args,
                                 PyObject *kwds) {
    Interpreter *self = (Interpreter *)PyType_GenericAlloc(type, 0);
    if (!self)
        return NULL;

    self->luafunction_type = NULL;
    self->L = NULL;

    ModuleState *state = PyType_GetModuleState(type);
    if (!state) {
        PyErr_SetString(PyExc_Exception, "module initialization error");
        goto error;
    }

    Py_INCREF(state->luafunction_type);
    self->luafunction_type = state->luafunction_type;

    self->L = lua_newstate(l_alloc, NULL);
    if (!self->L)
        goto error;

    lua_pushcfunction(self->L, init_lua_state);
    lua_pushlightuserdata(self->L, self);
    int err = lua_pcall(self->L, 1, 0, 0);
    if (err) {
        py_raise_lua_error(self->L);
        goto error;
    }

    clear_lua_stack(self->L);

    return (PyObject *)self;

error:

    if (self->L) {
        lua_close(self->L);
        self->L = NULL;
    }

    if (self->luafunction_type) {
        Py_DECREF(self->luafunction_type);
        self->luafunction_type = NULL;
    }

    Py_DECREF(self);
    return NULL;
}


static void Interpreter_dealloc(Interpreter *self) {
    if (self->L)
        lua_close(self->L);

    if (self->luafunction_type)
        Py_DECREF(self->luafunction_type);

    PyTypeObject *tp = Py_TYPE(self);
    PyObject_Free(self);
    Py_DECREF(tp);
}


static PyObject *Interpreter_load(Interpreter *self, PyObject *args) {
    const char *code;
    Py_ssize_t code_len;
    const char *name;
    if (!PyArg_ParseTuple(args, "s#z", &code, &code_len, &name))
        return NULL;

    PyThreadState *state = PyEval_SaveThread();

    int err = luaL_loadbufferx(self->L, code, code_len, name, "t");

    PyEval_RestoreThread(state);

    PyObject *result = NULL;

    if (err) {
        py_raise_lua_error(self->L);
        goto done;
    }

    lua_pushcfunction(self->L, lua_to_py);
    lua_insert(self->L, -2);
    err = lua_pcall(self->L, 1, 1, 0);
    if (err) {
        py_raise_lua_error(self->L);
        goto done;
    }

    result = get_pyobject(self->L, -1);
    if (!result)
        PyErr_SetString(PyExc_Exception, "invalid pyobject");

    Py_INCREF(result);

done:

    clear_lua_stack(self->L);

    return result;
}


static PyMethodDef interpreter_methods[] = {
    {.ml_name = "load",
     .ml_meth = (PyCFunction)Interpreter_load,
     .ml_flags = METH_VARARGS},
    {NULL}};


static PyType_Slot interpreter_type_slots[] = {
    {Py_tp_new, Interpreter_new},
    {Py_tp_dealloc, Interpreter_dealloc},
    {Py_tp_methods, interpreter_methods},
    {0, NULL}};


static PyType_Spec interpreter_type_spec = {
    .name = "hat.controller.interpreters._lua.Interpreter",
    .basicsize = sizeof(Interpreter),
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HEAPTYPE,
    .slots = interpreter_type_slots};


PyObject *create_interpreter_type(PyObject *module) {
    return PyType_FromModuleAndSpec(module, &interpreter_type_spec, NULL);
}


// [-0, +0, -]
Interpreter *get_interpreter(lua_State *L) {
    lua_rawgetp(L, LUA_REGISTRYINDEX, &interpreter_key);

    Interpreter *inter = lua_touserdata(L, -1);

    // TODO can poping of light user data raise error?
    lua_pop(L, 1);

    return inter;
}
