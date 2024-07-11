from __future__ import annotations

import logging
import os
import importlib.util
import enum

from types import ModuleType
from typing import List, Generator
from dataclasses import dataclass

log = logging.getLogger( __name__)

class ResultExecStatus(enum.Enum):
    SUCCESS = 'SUCCESS'
    FAILED  = 'FAILED'
    SKIPPED = 'SKIPPED'
    DRY_RUN = 'DRY_RUN'

@dataclass
class ResultExec():
    module: CDMSModuleLoader
    n_cmd:  int
    status: ResultExecStatus
    stdout: str = ''
    stderr: str = ''

class CDMSModuleLoader():
    def __init__(self, pyfile: str | None = None, path: str | None = None) -> None:
        """Load a py file as a module and get the CMDS list from it.
        If both pyfile and path are provided, the module will be loaded.

        Args:
            pyfile (str | None, optional): module name for spec. Defaults to None.
            path (str | None, optional): path to file. Defaults to None.
        """
        self.__pymodule: ModuleType | None = None
        self.__cmds: List[str] | None = None

        # Load module if pyfile and path are provided
        if pyfile is not None and path is not None:
            self.load_pyfile(pyfile, path)

    @property
    def module_name(self) -> str:
        """Getter for module name.

        Raises:
            ValueError: raise if module is not loaded yet.

        Returns:
            str: module name from spec
        """
        if self.__pymodule is not None:
            return self.__pymodule.__name__
        else:
            raise ValueError('Module not loaded yet')

    @property
    def module_path(self) -> str:
        """Getter for module path.

        Raises:
            ValueError: raise if module is not loaded yet.

        Returns:
            str: module path from spec
        """
        if self.__pymodule is not None:
            return str(self.__pymodule.__file__)
        else:
            raise ValueError('Module not loaded yet')

    @property
    def cmds(self) -> Generator[str, None, None]:
        """Return the CMDS list as a generator.

        Raises:
            ValueError: raise if CMDS is not loaded yet.

        Yields:
            Generator[str, None, None]: CMDS list as a generator
        """
        if isinstance(self.__cmds, list):
            for cmd in self.__cmds:
                yield cmd
        else:
            raise ValueError('CMDS not loaded yet')

    def load_pyfile(self, pyfile: str, path: str) -> None:
        """Load a py file as a module and get the CMDS list from it.

        Args:
            pyfile (str): module name for spec
            path (str): path to file

        Raises:
            ImportError: raise if module already loaded in current instance
            ImportError: raise if failed to load module
            ImportError: raise if failed to execute module
            ValueError: raise if CMDS with List type not found in module
        """
        if self.__pymodule is not None:
            raise ImportError('Module already loaded')

        spec = importlib.util.spec_from_file_location(pyfile, os.path.join(path, pyfile))
        if spec is None or spec.loader is None:
            raise ImportError(f'Failed to load module from [{os.path.join(path, pyfile)}]')

        self.__pymodule = importlib.util.module_from_spec(spec)
        if self.__pymodule is None:
            raise ImportError(f'Failed to load module from [{os.path.join(path, pyfile)}]')

        try:
            spec.loader.exec_module(self.__pymodule)
        except Exception as err:
            # if failed to execute module, reraise any as ImportErrors
            raise ImportError(f'Failed to execute module [{os.path.join(path, pyfile)}]: {err}') from err
        log.debug('Executed module [%s]', self.__pymodule.__name__)

        self.__cmds = getattr(self.__pymodule, 'CMDS', None)
        if self.__cmds is None or not isinstance(self.__cmds, List):
            raise ValueError(f'CMDS with List type not found in [{os.path.join(path, pyfile)}]')
        log.debug('Found CMDS [%s]', self.__cmds)
