from hat.doit.c import (get_py_c_flags,
                        get_py_ld_flags,
                        get_py_ld_libs,
                        CBuild)

from .. import common


__all__ = ['task_pymodules_quickjs',
           'task_pymodules_quickjs_obj',
           'task_pymodules_quickjs_dep',
           'task_pymodules_quickjs_cleanup']


quickjs_path = (common.src_py_dir / 'hat/controller/interpreters/_quickjs'
                ).with_suffix(common.py_ext_suffix)
quickjs_files = ['cutils.c', 'libbf.c', 'libregexp.c', 'libunicode.c',
                 'quickjs.c', 'unicode_gen.c']
quickjs_src_paths = [*(common.src_c_dir / 'py/quickjs').rglob('*.c'),
                     *((common.peru_dir / 'quickjs') / i
                       for i in quickjs_files)]
quickjs_build_dir = (common.build_pymodules_dir / 'quickjs' /
                     f'{common.target_platform.name.lower()}_'
                     f'{common.target_py_version.name.lower()}')
quickjs_c_flags = [
    *get_py_c_flags(py_limited_api=common.py_limited_api),
    f"-I{common.peru_dir / 'quickjs'}",
    '-fPIC',
    '-D_GNU_SOURCE',
    '-DCONFIG_VERSION="2024-01-13"',
    '-O2',
    # '-ggdb'
    ]
quickjs_ld_flags = [*get_py_ld_flags(py_limited_api=common.py_limited_api)]
quickjs_ld_libs = [*get_py_ld_libs(py_limited_api=common.py_limited_api)]

quickjs_build = CBuild(src_paths=quickjs_src_paths,
                       build_dir=quickjs_build_dir,
                       c_flags=quickjs_c_flags,
                       ld_flags=quickjs_ld_flags,
                       ld_libs=quickjs_ld_libs,
                       task_dep=['pymodules_quickjs_cleanup',
                                 'peru'])


def task_pymodules_quickjs():
    """Build pymodules quickjs"""
    yield from quickjs_build.get_task_lib(quickjs_path)


def task_pymodules_quickjs_obj():
    """Build pymodules quickjs .o files"""
    yield from quickjs_build.get_task_objs()


def task_pymodules_quickjs_dep():
    """Build pymodules quickjs .d files"""
    yield from quickjs_build.get_task_deps()


def task_pymodules_quickjs_cleanup():
    """Cleanup pymodules quickjs"""

    def cleanup():
        for path in quickjs_path.parent.glob('_quickjs.*'):
            if path == quickjs_path:
                continue
            common.rm_rf(path)

    return {'actions': [cleanup]}
