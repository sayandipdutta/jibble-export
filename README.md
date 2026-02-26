# Jibble Export

## Getting Started

### Pre-requisite

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation)
1. Clone this repository
1. Create new API credentials at [Jibble API Credentials](https://web.jibble.io/organization/api)
1. Create a `.env` file inside cloned repo directory, with following content:

```env
JIBBLE_CLIENT_ID=<copied client_id after Credentials Creation>
JIBBLE_CLIENT_SECRET=<copied client_secret after Credentials Creation>
```

### Usage

There are two ways to use the CLI:

1. Install the CLI:

```
uv tool install .
```

This method will enable you to invoke the CLI from anywhere, globally. You can run commands like:

```
jibble --help
```

2. Run CLI using `uv` without installing it globally.

```
cd jibble-export
uv run jibble --help
```

## Features

### clock in

```shell
$ jibble clockin
Successfully Jibbled in!
```

With auto clock out set:

```shell
$ jibble clockin --autoout PT9H
Successfully Jibbled in! Auto clock out set after 9:00:00!
```

The `autoout` argument must be in ISO 8601 time delta format.

### clock out

```shell
$ jibble clockout
Successfully Jibbled out!
```

### Exporting attendance report

```shell
$ jibble export --help
usage: jibble export [-h] [--calendar CALENDAR] [--outfile OUTFILE] [--duration DURATION] [--json]

options:
  -h, --help            show this help message and exit
  --calendar, -c CALENDAR
                        Name of the calendar
  --outfile, -o OUTFILE
                        Path to the exported file
  --duration, -d DURATION
                        Export attendance report for given duration.

                        If duration is not provided, then report is exported for current month, year.

                        Outfile filename is guessed from duration.

                        Duration format:
                            $ jibble export --duration "2026-02-01:2026-02-28"
                            # Report successfully exported to attendance_report_2026-02-01_2026-02-28.xlsx
                            $ jibble export --duration feb
                            # Report successfully exported to attendance_report_FEBRUARY-2026.xlsx
                            $ jibble export --duration feb,2026
                            # Report successfully exported to attendance_report_FEBRUARY-2026.xlsx
                            $ jibble export --duration 2026
                            # Report successfully exported to attendance_report_2026.xlsx

                          Special values:
                          If LAST_ONE_MONTH report is exported on 24th Feb, 2026
                            $ jibble export --duration LAST_ONE_MONTH
                            # Report successfully exported to attendance_report_2026-01-25_2026-02-24.xlsx
                          If LAST_MONTH report is exported in Feb, 2026
                            $ jibble export --duration LAST_MONTH
                            # Report successfully exported to attendance_report_JANUARY-2026.xlsx

                        When date format is used, it has to be in yyyy-mm-dd format.
  --json                create reports/latest.json with export information. Useful for CI.
```

### Getting help

Type `jibble --help` for listing available commands. Type `jibble {command} --help` for help on individual commands.

## Useful recipes

### Clockin at logon in Windows

```batch
# script.bat
@echo off
pushd <path/to/jibble-export>
uv run jibble export clockin --autoout PT9H
popd
```

Either create a new task at log on, using task scheduler, or put it in `shell:startup`

### Clockin at logon in linux (using systemd)

```shell
!#/bin/env sh
# script.sh
cd <path/to/jibble-export>
uv run jibble export clockin --autoout PT9H
```

Then make it executable:

```shell
chmod +x script.sh
```

Put its full path in `~/.profile` for bash or `~/.zprofile` for zsh, or at `$PROFILE`

_**NOTE**: This library is primarily for personal use._
