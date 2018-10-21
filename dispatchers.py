import subprocess
from abc import ABC, abstractmethod


class _Dispatcher(ABC):
    @abstractmethod
    def dispatch(self, command):
        pass

    @abstractmethod
    def wait(self):
        pass


class PythonSubprocessDispatcher(_Dispatcher):
    def __init__(self):
        self.processes = []

    def dispatch(self, command):
        process = subprocess.Popen(command, shell=True)
        self.processes.append(process)

    def wait(self):
        for process in self.processes:
            process.wait()


class DRMAADispatcher(_Dispatcher):
    def __init__(self):
        import drmaa

        self.jobids = []
        self.session = drmaa.Session()
        self.session.initialize()

    def dispatch(self, command):
        jt = self.session.createJobTemplate()
        jt.remoteCommand = command

        jobid = self.session.runJob(jt)
        self.jobids.append(jobid)

    def wait(self):
        self.session.synchronize(self.jobids)
