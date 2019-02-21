from typing import Optional, Collection


class JobTemplate:
    remoteCommand = ...  # type: str

    def __init__(self, errorPath: Optional[str] = None): ...


class Session:
    def initialize(self) -> None: ...

    def runJob(self, jobTemplate: JobTemplate) -> str: ...

    def wait(self, jobid: str) -> None: ...

    def synchronize(self, jobIds: Collection[str]) -> None: ...
