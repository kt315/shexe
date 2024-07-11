### Get

```
git clone https://github.com/kt315/shexe.git
cd shexe/
python -m venv --prompt v .venv
. .venv/bin/activate
./shellexecutor.py -h
./shellexecutor.py -t ./tests/
```

### Usage

Params:
```
$ ./shellexecutor.py -h
usage: Shell Executor [-h] [-d] [-t] rootdir

Execute shell commands from py files

positional arguments:
  rootdir        Root directory to search for py files

options:
  -h, --help     show this help message and exit
  -d, --debug    Enable debug mode
  -t, --dry-run  Enable dry-run mode
```

`dry-run` mode will not execute commands, but show which commands will be skipped.\
`debug` more logs.
