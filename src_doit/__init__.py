from .pymodules import *  # NOQA

from pathlib import Path
import sys

from hat.doit import common
from hat.doit.c import get_task_clang_format
from hat.doit.docs import (build_sphinx,
                           build_pdoc)
from hat.doit.py import (get_task_build_wheel,
                         get_task_run_pytest,
                         get_task_create_pip_requirements,
                         run_flake8,
                         get_py_versions)

from . import pymodules


__all__ = ['task_clean_all',
           'task_build',
           'task_check',
           'task_test',
           'task_docs',
           'task_format',
           'task_peru',
           'task_json_schema_repo',
           'task_pip_requirements',
           *pymodules.__all__]


build_dir = Path('build')
docs_dir = Path('docs')
pytest_dir = Path('test_pytest')
schemas_json_dir = Path('schemas_json')
src_c_dir = Path('src_c')
src_py_dir = Path('src_py')

build_py_dir = build_dir / 'py'
build_docs_dir = build_dir / 'docs'

json_schema_repo_path = src_py_dir / 'hat/controller/json_schema_repo.json'

py_limited_api = next(iter(common.PyVersion))


def task_clean_all():
    """Clean all"""
    return {'actions': [(common.rm_rf, [
        build_dir,
        json_schema_repo_path,
        *(src_py_dir / 'hat/controller/interpreters').glob('*.so'),
        *(src_py_dir / 'hat/controller/interpreters').glob('*.pyd')
        ])]}


def task_build():
    """Build"""
    return get_task_build_wheel(src_dir=src_py_dir,
                                build_dir=build_py_dir,
                                py_versions=get_py_versions(py_limited_api),
                                py_limited_api=py_limited_api,
                                platform=common.target_platform,
                                is_purelib=False,
                                task_dep=['json_schema_repo',
                                          'pymodules'])


def task_check():
    """Check with flake8"""
    return {'actions': [(run_flake8, [src_py_dir]),
                        (run_flake8, [pytest_dir])]}


def task_test():
    """Test"""
    return get_task_run_pytest(task_dep=['json_schema_repo',
                                         'pymodules'])


def task_docs():
    """Docs"""

    def build():
        build_sphinx(src_dir=docs_dir,
                     dst_dir=build_docs_dir,
                     project='hat-controller',
                     extensions=['sphinxcontrib.programoutput'])
        build_pdoc(module='hat.controller',
                   dst_dir=build_docs_dir / 'py_api')

    return {'actions': [build],
            'task_dep': ['json_schema_repo']}


def task_format():
    """Format"""
    yield from get_task_clang_format([*(src_c_dir / 'py').rglob('*.c'),
                                      *(src_c_dir / 'py').rglob('*.h')])


def task_peru():
    """Peru"""
    return {'actions': [f'{sys.executable} -m peru sync']}


def task_json_schema_repo():
    """Generate JSON Schema Repository"""
    return common.get_task_json_schema_repo(schemas_json_dir.rglob('*.yaml'),
                                            json_schema_repo_path)


def task_pip_requirements():
    """Create pip requirements"""
    return get_task_create_pip_requirements()
