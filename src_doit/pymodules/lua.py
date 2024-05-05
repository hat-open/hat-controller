from hat.doit.c import (get_py_c_flags,
                        get_py_ld_flags,
                        get_py_ld_libs,
                        CBuild)

from .. import common


__all__ = ['task_pymodules_lua',
           'task_pymodules_lua_obj',
           'task_pymodules_lua_dep',
           'task_pymodules_lua_cleanup']


lua_path = (common.src_py_dir / 'hat/controller/interpreters/_lua'
            ).with_suffix(common.py_ext_suffix)
lua_core_files = ['lapi.c',
                  'lcode.c',
                  'lctype.c',
                  'ldebug.c',
                  'ldo.c',
                  'ldump.c',
                  'lfunc.c',
                  'lgc.c',
                  'llex.c',
                  'lmem.c',
                  'lobject.c',
                  'lopcodes.c',
                  'lparser.c',
                  'lstate.c',
                  'lstring.c',
                  'ltable.c',
                  'ltm.c',
                  'lundump.c',
                  'lvm.c',
                  'lzio.c']
lua_lib_files = ['lauxlib.c',
                 'lbaselib.c',
                 'lcorolib.c',
                 'lmathlib.c',
                 'lstrlib.c',
                 'ltablib.c',
                 'lutf8lib.c']
lua_files = [*lua_core_files, *lua_lib_files]
lua_src_paths = [*(common.src_c_dir / 'py/lua').rglob('*.c'),
                 *((common.peru_dir / 'lua/src') / i
                   for i in lua_files)]
lua_build_dir = (common.build_pymodules_dir / 'lua' /
                 f'{common.target_platform.name.lower()}_'
                 f'{common.target_py_version.name.lower()}')
lua_c_flags = [
    *get_py_c_flags(py_limited_api=common.py_limited_api),
    f"-I{common.peru_dir / 'lua/src'}",
    '-fPIC',
    '-D_GNU_SOURCE',
    '-O2',
    # '-O0', '-ggdb'
    ]
lua_ld_flags = [*get_py_ld_flags(py_limited_api=common.py_limited_api)]
lua_ld_libs = [*get_py_ld_libs(py_limited_api=common.py_limited_api)]

lua_build = CBuild(src_paths=lua_src_paths,
                   build_dir=lua_build_dir,
                   c_flags=lua_c_flags,
                   ld_flags=lua_ld_flags,
                   ld_libs=lua_ld_libs,
                   task_dep=['pymodules_lua_cleanup',
                             'peru'])


def task_pymodules_lua():
    """Build pymodules lua"""
    yield from lua_build.get_task_lib(lua_path)


def task_pymodules_lua_obj():
    """Build pymodules lua .o files"""
    yield from lua_build.get_task_objs()


def task_pymodules_lua_dep():
    """Build pymodules lua .d files"""
    yield from lua_build.get_task_deps()


def task_pymodules_lua_cleanup():
    """Cleanup pymodules lua"""

    def cleanup():
        for path in lua_path.parent.glob('_lua.*'):
            if path == lua_path:
                continue
            common.rm_rf(path)

    return {'actions': [cleanup]}
