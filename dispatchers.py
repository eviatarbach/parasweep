import subprocess
from abc import ABC, abstractmethod


class _Dispatcher(ABC):

    @abstractmethod
    def dispatch(self, command):
        pass

    def wait(self):
        pass


class PythonSubprocessDispatcher(_Dispatcher):

    def dispatch(self, command):
        self.process = subprocess.Popen(command, shell=True)
        return self

    def wait(self):
        self.process.wait()
