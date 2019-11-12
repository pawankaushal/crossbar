import os
import pathlib
import shlex
import shutil
import subprocess

import snapcraft


class PythonPlugin(snapcraft.BasePlugin):
    @classmethod
    def schema(cls):
        schema = super().schema()
        schema['properties']['python-packages'] = {
            'type': 'array',
            'minitems': 1,
            'uniqueItems': True,
            'items': {'type': 'string'},
            'default': [],
        }
        schema['anyOf'] = [{'required': ['source']}, {'required': ['python-packages']}]
        return schema

    @classmethod
    def get_pull_properties(cls):
        return ['python-packages']

    def _enable_py38_ppa(self):
        self._run('apt install software-properties-common -y')
        self._run('add-apt-repository ppa:deadsnakes/ppa -y')

    def _ensure_py38(self):
        self._run('apt install python3.8 python3.8-venv python3.8-dev -y')

    def _run(self, command, cwd=None):
        subprocess.check_call(shlex.split(command), cwd=cwd)

    def build(self):
        super().build()
        self._ensure_py38()
        self._run('ln -s python3.8 python3', cwd=os.path.join(self.installdir, 'usr/bin'))
        self._run('ln -s python3.8 python', cwd=os.path.join(self.installdir, 'usr/bin'))

        target = os.path.join(self.installdir, 'crossbar')
        if os.path.exists(target):
            shutil.rmtree(target)
            pathlib.Path(target).mkdir()

        if self.options.python_packages and '__none__' in self.options.python_packages:
            return

        if self.options.source:
            self._run('/usr/bin/python3.8 -m pip install --no-compile -t {} .'.format(target))

        if self.options.python_packages:
            packages = ' '.join(self.options.python_packages)
            self._run('/usr/bin/python3.8 -m pip install --no-compile -t {} {}'.format(target, packages))

        for filename in pathlib.Path(target).rglob('*.so'):
            self._run("strip -s {}".format(filename))

    @property
    def stage_packages(self):
        self._enable_py38_ppa()
        packages = super().stage_packages
        if 'python3.8' not in packages:
            packages.append('python3.8')
        return packages