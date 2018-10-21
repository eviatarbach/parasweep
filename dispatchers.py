import subprocess
from abc import ABC, abstractmethod


class _Dispatcher(ABC):
    def __init__(self):
        pass

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


class DRMAADispatcher(_Dispatcher):
    def __init__(self):
        import drmaa

        self.session = drmaa.Session()
        self.session.initialize()

    def dispatch(self, command):
        jt = self.session.createJobTemplate()
        jt.remoteCommand = command

        jobid = self.session.runJob(jt)
