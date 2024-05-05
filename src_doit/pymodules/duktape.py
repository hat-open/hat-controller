from hat.doit.c import (get_py_c_flags,
                        get_py_ld_flags,
                        get_py_ld_libs,
                        CBuild)

from .. import common


__all__ = ['task_pymodules_duktape',
           'task_pymodules_duktape_obj',
           'task_pymodules_duktape_dep',
           'task_pymodules_duktape_cleanup']


duktape_path = (common.src_py_dir / 'hat/controller/interpreters/_duktape'
                ).with_suffix(common.py_ext_suffix)
duktape_src_paths = [*(common.src_c_dir / 'py/duktape').rglob('*.c'),
                     *(common.peru_dir / 'duktape/src').rglob('*.c')]
duktape_build_dir = (common.build_pymodules_dir / 'duktape' /
                     f'{common.target_platform.name.lower()}_'
                     f'{common.target_py_version.name.lower()}')
duktape_c_flags = [
    *get_py_c_flags(py_limited_api=common.py_limited_api),
    f"-I{common.peru_dir / 'duktape/src'}",
    '-fPIC',
    '-D_GNU_SOURCE',
    '-O2',
    # '-O0', '-ggdb'
    ]
duktape_ld_flags = [*get_py_ld_flags(py_limited_api=common.py_limited_api)]
duktape_ld_libs = [*get_py_ld_libs(py_limited_api=common.py_limited_api)]

duktape_build = CBuild(src_paths=duktape_src_paths,
                       build_dir=duktape_build_dir,
                       c_flags=duktape_c_flags,
                       ld_flags=duktape_ld_flags,
                       ld_libs=duktape_ld_libs,
                       task_dep=['pymodules_duktape_cleanup',
                                 'peru'])


def task_pymodules_duktape():
    """Build pymodules duktape"""
    yield from duktape_build.get_task_lib(duktape_path)


def task_pymodules_duktape_obj():
    """Build pymodules duktape .o files"""
    yield from duktape_build.get_task_objs()


def task_pymodules_duktape_dep():
    """Build pymodules duktape .d files"""
    yield from duktape_build.get_task_deps()


def task_pymodules_duktape_cleanup():
    """Cleanup pymodules duktape"""

    def cleanup():
        for path in duktape_path.parent.glob('_duktape.*'):
            if path == duktape_path:
                continue
            common.rm_rf(path)

    return {'actions': [cleanup]}
