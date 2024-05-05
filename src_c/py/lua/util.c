#include "util.h"


static int clear(lua_State *L) {
    lua_settop(L, 0);
    return 0;
}


void clear_lua_stack(lua_State *L) {
    int top = lua_gettop(L);
    if (top < 1)
        return;

    lua_pushcfunction(L, clear);
    if (lua_pcall(L, top, 0, 0)) {
        // TODO pop error without raising error
    }
}
