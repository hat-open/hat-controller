from pathlib import Path

from hat.doit import common
from hat.doit.c import (get_py_ext_suffix,
                        get_py_c_flags,
                        get_py_ld_flags,
                        get_py_ld_libs,
                        CBuild)


__all__ = ['task_pymodules_duktape',
           'task_pymodules_duktape_obj',
           'task_pymodules_duktape_dep',
           'task_pymodules_duktape_cleanup']


py_limited_api = next(iter(common.PyVersion))
py_ext_suffix = get_py_ext_suffix(py_limited_api=py_limited_api)

build_dir = Path('build')
peru_dir = Path('peru')
src_c_dir = Path('src_c')
src_py_dir = Path('src_py')

pymodules_build_dir = build_dir / 'pymodules'

duktape_path = (src_py_dir / 'hat/controller/interpreters/_duktape'
                ).with_suffix(py_ext_suffix)
duktape_src_paths = [*(src_c_dir / 'py/duktape').rglob('*.c'),
                     *(peru_dir / 'duktape/src').rglob('*.c')]
duktape_build_dir = (pymodules_build_dir / 'duktape' /
                     f'{common.target_platform.name.lower()}_'
                     f'{common.target_py_version.name.lower()}')
duktape_c_flags = [
    *get_py_c_flags(py_limited_api=py_limited_api),
    f"-I{peru_dir / 'duktape/src'}",
    '-fPIC',
    '-D_GNU_SOURCE',
    '-O2',
    # '-O0', '-ggdb'
    ]
duktape_ld_flags = [*get_py_ld_flags(py_limited_api=py_limited_api)]
duktape_ld_libs = [*get_py_ld_libs(py_limited_api=py_limited_api)]

duktape_build = CBuild(src_paths=duktape_src_paths,
                       build_dir=duktape_build_dir,
                       c_flags=duktape_c_flags,
                       ld_flags=duktape_ld_flags,
                       ld_libs=duktape_ld_libs,
                       task_dep=['pymodules_quickjs_cleanup',
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
