#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
import os
import argparse
import subprocess

from typing import Generator, Dict

from shexec.shexec import CDMSModuleLoader, ResultExecStatus, ResultExec

log = logging.getLogger('shellexecutor' if __name__ == '__main__' else __name__)

def search_py_files(rootdir: str) -> Generator[Dict[str, str], None, None]:
    """Search for python files in the given root directory

    Args:
        rootdir (str): starting directory to search for python files

    Yields:
        Generator[Dict[str, str], None, None]: dictionary containing the
        directory path and filename
    """
    try:
        # symlink also will be considered as file
        if os.path.isfile(rootdir) and rootdir.endswith('.py'):
            yield {'dirpath': os.path.dirname(rootdir),
                    'filename': os.path.basename(rootdir)}

        # symlink also will be considered as directory
        elif os.path.isdir(rootdir):
            for entry in sorted(os.listdir(rootdir)):
                full_path = os.path.join(rootdir, entry)
                if os.path.isfile(full_path) and full_path.endswith('.py'):
                    yield {'dirpath': rootdir,
                           'filename': entry}

                elif os.path.isdir(full_path):
                    yield from search_py_files(full_path)

                else:
                    log.debug("Warn: [%s] is not a valid file or directory. Skipped", full_path)
        else:
            log.debug("Warn: [%s] is not a valid file or directory. Skipped", rootdir)

    except FileNotFoundError:
        log.debug("Warn: File not found for [%s]. Skipped", rootdir)
    except PermissionError:
        log.debug("Warn: Permission denied for [%s]. Skipped", rootdir)
    except OSError as e:
        log.error("Error: [%s]", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        "Shell Executor", description="Execute shell commands from py files")
    parser.add_argument('rootdir', help='Root directory to search for py files')
    parser.add_argument('-d', '--debug',
                        action='store_true', help='Enable debug mode')
    parser.add_argument('-t', '--dry-run',
                        action='store_true', help='Enable dry-run mode')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s [%(levelname)s]: %(message)s')

    if args.dry_run:
        log.info('== Dry-run mode enabled. Commands will NOT be executed ==')

    results_exec = {}
    for pyfile in search_py_files(args.rootdir):
        log.debug('>> Found [%s] in [%s]',
                  pyfile['filename'], pyfile['dirpath'])
        try:
            executor = CDMSModuleLoader(pyfile=pyfile['filename'],
                                        path=pyfile['dirpath'])
        except (ImportError, ValueError) as err:
            log.warning('Failed to load module [%s] from [%s]. Skipped: %s',
                        pyfile['filename'], pyfile['dirpath'], err)
            continue

        for n_cmd, cmd in enumerate(executor.cmds):
            log.debug('Executing [%s] from [%s]', cmd, pyfile['filename'])

            res_exec = None
            # skip if command already executed earlier
            if cmd in results_exec:
                res_exec = ResultExec(
                    module=executor,
                    n_cmd=n_cmd,
                    status=ResultExecStatus.SKIPPED)
                log.info('Skipped cmd [%s] from [%s] number [%s]. Command already executed.',
                         cmd, res_exec.module.module_path, n_cmd)
                results_exec[cmd].append(res_exec)
                continue

            if not args.dry_run:
                try:
                    result_run = subprocess.run(
                        cmd, shell=True, check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

                    res_exec = ResultExec(
                        module=executor, n_cmd=n_cmd,
                        status=ResultExecStatus.SUCCESS     \
                            if result_run.returncode == 0   \
                            else ResultExecStatus.FAILED,
                        stdout=result_run.stdout.decode('utf-8'),
                        stderr=result_run.stderr.decode('utf-8'))

                except (FileNotFoundError, OSError) as f_err:
                    res_exec = ResultExec(
                        module=executor, n_cmd=n_cmd,
                        status=ResultExecStatus.FAILED,
                        stderr=str(f_err))

            else:
                res_exec = ResultExec(
                    module=executor, n_cmd=n_cmd,
                    status=ResultExecStatus.DRY_RUN)

            # pylint: disable=logging-not-lazy
            results_exec[cmd] = [res_exec]
            log.info('Executed cmd [%s] from [%s] number [%s] status [%s]' +
                     f"{'\n\tstdout [%s] stderr [%s]' if not args.dry_run else '%s%s'}",
                     cmd, res_exec.module.module_path, n_cmd,
                     res_exec.status.value,
                     res_exec.stdout.strip() if not args.dry_run else '',
                     res_exec.stderr.strip() if not args.dry_run else '')
            # pylint: enable=logging-not-lazy


if __name__ == '__main__':
    main()
