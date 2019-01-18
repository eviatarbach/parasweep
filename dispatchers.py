"""Dispatchers for running parallel jobs."""
import subprocess
from abc import ABC, abstractmethod


class _Dispatcher(ABC):
    @abstractmethod
    def initialize_session(self):
        """Must be called before dispatching jobs."""
        pass

    @abstractmethod
    def dispatch(self, command, wait):
        """
        Dispatch a command using the dispatcher.

        Parameters
        ----------
        command : str
            The command to dispatch.
        wait : bool
            Whether to wait for the process to finish before returning.

        """
        pass

    @abstractmethod
    def wait_all(self):
        """Wait for the running/scheduled processes to finish, then return."""
        pass


class PythonSubprocessDispatcher(_Dispatcher):
    def initialize_session(self):
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
        if job_template is None:
            import drmaa

            self.job_template = drmaa.JobTemplate()
        else:
            self.job_template = job_template

    def initialize_session(self):
        # Ensure there is only one active DRMAA session, otherwise it raises
        # an error
        if DRMAADispatcher.session is None:
            import drmaa

            self.session = drmaa.Session()
            self.session.initialize()
            DRMAADispatcher.session = self.session
        else:
            self.session = DRMAADispatcher.session

        self.jobids = []

    def dispatch(self, command, wait):
        self.job_template.remoteCommand = command

        jobid = self.session.runJob(self.job_template)
        self.jobids.append(jobid)
        if wait:
            self.session.wait(jobid)

    def wait_all(self):
        self.session.synchronize(self.jobids)
