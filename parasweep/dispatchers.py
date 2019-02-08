"""Dispatchers for running parallel jobs."""
import subprocess
from abc import ABC, abstractmethod


class Dispatcher(ABC):
    """
    Abstract base class for dispatchers.

    Subclasses should implement the ``initialize_session``, ``dispatch``, and
    ``wait_all`` methods.

    """

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


class PythonSubprocessDispatcher(Dispatcher):
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


class DRMAADispatcher(Dispatcher):
    """
    Dispatcher for DRMAA.

    Parameters
    ----------
    job_template : drmaa.JobTemplate instance, optional
        A job template containing settings for running the jobs with
        the job scheduler. Documentation for the different options is
        available in the Python drmaa package. Some options specific to each
        job scheduler, called the native specification, may have to be set
        using the ``job_template.nativeSpecification`` attribute, the options
        for which can be found in the job scheduler's DRMAA interface (e.g.,
        slurm-drmaa for Slurm and pbs-drmaa for PBS).

    Examples
    --------
    >>> import drmaa
    >>> jt = drmaa.JobTemplate(hardWallclockTimeLimit=60)
    >>> dispatcher = DRMAADispatcher(jt)

    """
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
