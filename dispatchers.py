import subprocess
from abc import ABC, abstractmethod


class _Dispatcher(ABC):
    @abstractmethod
    def dispatch(self, command, wait):
        pass

    @abstractmethod
    def wait_all(self):
        pass


class PythonSubprocessDispatcher(_Dispatcher):
    def __init__(self):
        self.processes = []

    def dispatch(self, command, wait):
        process = subprocess.Popen(command, shell=True)
        self.processes.append(process)
        if wait:
            process.wait()

    def wait_all(self):
        for process in self.processes:
            process.wait()


class DRMAADispatcher(_Dispatcher):
    session = None

    def __init__(self, job_template=None):
        # Ensure there is only one active DRMAA session, otherwise it raises
        # an error
        if DRMAADispatcher.session is None:
            import drmaa

            self.session = drmaa.Session()
            self.session.initialize()
            DRMAADispatcher.session = self.session
        else:
            self.session = DRMAADispatcher.session

        if job_template is None:
            self.job_template = self.session.createJobTemplate()
        else:
            self.job_template = job_template

        self.jobids = []

    def dispatch(self, command, wait):
        self.job_template.remoteCommand = command

        jobid = self.session.runJob(self.job_template)
        self.jobids.append(jobid)
        if wait:
            self.session.wait(jobid)

    def wait_all(self):
        self.session.synchronize(self.jobids)
