from .pymodules import *  # NOQA

import sys

from hat.doit.c import get_task_clang_format
from hat.doit.docs import (build_sphinx,
                           build_pdoc)
from hat.doit.py import (get_task_build_wheel,
                         get_task_run_pytest,
                         get_task_create_pip_requirements,
                         run_flake8,
                         get_py_versions)

from . import pymodules
from . import common


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


json_schema_repo_path = (common.src_py_dir /
                         'hat/controller/json_schema_repo.json')


def task_clean_all():
    """Clean all"""
    return {'actions': [(common.rm_rf, [
        common.build_dir,
        json_schema_repo_path,
        *(common.src_py_dir / 'hat/controller/interpreters').glob('*.so'),
        *(common.src_py_dir / 'hat/controller/interpreters').glob('*.pyd')
        ])]}


def task_build():
    """Build"""
    return get_task_build_wheel(
        src_dir=common.src_py_dir,
        build_dir=common.build_py_dir,
        py_versions=get_py_versions(common.py_limited_api),
        py_limited_api=common.py_limited_api,
        platform=common.target_platform,
        is_purelib=False,
        task_dep=['json_schema_repo',
                  'pymodules'])


def task_check():
    """Check with flake8"""
    return {'actions': [(run_flake8, [common.src_py_dir]),
                        (run_flake8, [common.pytest_dir])]}


def task_test():
    """Test"""
    return get_task_run_pytest(task_dep=['json_schema_repo',
                                         'pymodules'])


def task_docs():
    """Docs"""

    def build():
        build_sphinx(src_dir=common.docs_dir,
                     dst_dir=common.build_docs_dir,
                     project='hat-controller',
                     extensions=['sphinxcontrib.programoutput'])
        build_pdoc(module='hat.controller',
                   dst_dir=common.build_docs_dir / 'py_api')

    return {'actions': [build],
            'task_dep': ['json_schema_repo']}


def task_format():
    """Format"""
    yield from get_task_clang_format([*(common.src_c_dir / 'py').rglob('*.c'),
                                      *(common.src_c_dir / 'py').rglob('*.h')])


def task_peru():
    """Peru"""
    return {'actions': [f'{sys.executable} -m peru sync']}


def task_json_schema_repo():
    """Generate JSON Schema Repository"""
    return common.get_task_json_schema_repo(
        common.schemas_json_dir.rglob('*.yaml'), json_schema_repo_path)


def task_pip_requirements():
    """Create pip requirements"""
    return get_task_create_pip_requirements()
