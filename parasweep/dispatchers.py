"""Dispatchers for running parallel jobs."""
import subprocess
import multiprocessing
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, List


class Dispatcher(ABC):
    """
    Abstract base class for dispatchers.

    Subclasses should implement the ``initialize_session``, ``dispatch``, and
    ``wait_all`` methods.

    """

    @abstractmethod
    def initialize_session(self) -> None:
        """Must be called before dispatching jobs."""
        pass

    @abstractmethod
    def dispatch(self, command: str, wait: bool) -> None:
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
    def wait_all(self) -> None:
        """Wait for the running/scheduled processes to finish, then return."""
        pass


class SubprocessDispatcher(Dispatcher):
    """
    Dispatcher using subprocesses.

    Parameters
    ----------
    max_procs : int, optional
        The maximum number of processes to run simultaneously. By default, uses
        the number of processors on the machine (this is a good choice for
        CPU-bound work).

    """

    def __init__(self, max_procs: Optional[int] = None):
        self.max_procs = (multiprocessing.cpu_count() if max_procs is None
                          else max_procs)

    def initialize_session(self) -> None:
        self.processes = []  # type: List[Future[int]]

        self.pool = ThreadPoolExecutor(max_workers=self.max_procs)

    def dispatch(self, command: str, wait: bool) -> None:
        process = self.pool.submit(lambda: subprocess.Popen(command,
                                                            shell=True).wait())
        self.processes.append(process)

        if wait:
            process.result()

    def wait_all(self) -> None:
        for process in self.processes:
            process.result()


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
    import drmaa
    session = None  # type: drmaa.Session

    def __init__(self, job_template: Optional[drmaa.JobTemplate] = None):
        if job_template is None:
            import drmaa

            self.job_template = drmaa.JobTemplate()
        else:
            self.job_template = job_template

    def initialize_session(self) -> None:
        # Ensure there is only one active DRMAA session, otherwise it raises
        # an error
        if DRMAADispatcher.session is None:
            import drmaa

            self.session = drmaa.Session()
            self.session.initialize()
            DRMAADispatcher.session = self.session
        else:
            self.session = DRMAADispatcher.session

        self.jobids = []  # type: List[str]

    def dispatch(self, command: str, wait: bool) -> None:
        self.job_template.remoteCommand = command

        jobid = self.session.runJob(self.job_template)
        self.jobids.append(jobid)
        if wait:
            self.session.wait(jobid)

    def wait_all(self) -> None:
        self.session.synchronize(self.jobids)
