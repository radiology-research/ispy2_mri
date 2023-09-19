# ispy2_mri

[![PyPI - Version](https://img.shields.io/pypi/v/ispy2-mri.svg)](https://pypi.org/project/ispy2-mri)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ispy2-mri.svg)](https://pypi.org/project/ispy2-mri)

-----

**Table of Contents**

- [ispy2\_mri](#ispy2_mri)
  - [Purpose](#purpose)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Program Setup](#program-setup)
  - [License](#license)

## Purpose
This package provide a graphical application to enter information about batches of MRI's as they come in from sites.  The information is saved in the ispy2 database, named `breastdb` on the server.  Some of that information is available electronically, and can be pulled from a plain text file of the user's choice instead of entered manually.

This is a replacement for *one* of the functions currently accessible through a web interface.  That web application can still be used for other things, like generating reports, or even for entering the same information.  However, the web application does not use the information in the plain text files.

## Installation

### Prerequisites
   * Only tested on MS-Windows, might work elsewhere if ODBC does
   * Python 3.10 or greater installed.  To test, start a terminal (hit the Windows button, type "command prompt", and select that application), and enter `py --version` in the terminal.
   * 64-bit ODBC installed with a recent MS SQL Server driver, e.g., 18.
   * An ODBC data source ("DSN") named `breastdb-new` pointing to the breastdb database.
   * You have permission to write to that database.
   * The machine you are using can contact the database (may require firewall changes)
   * You have access to the directory in which the text files summarizing key scan info are available.

### Program Setup
The main issue is exactly how you get access to the Python Package that uses the program.

```console
pip install ispy2-mri
```

This will create a program that can be launched from a terminal with `ispy2-mri`.  You may want to create a desktop shortcut that will do the same thing.

## License

`ispy2-mri` is distributed under the terms of the [GPL-3](https://www.gnu.org/licenses/gpl-3.0.en.html) license.
