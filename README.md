# Python

A reference guide for Python.

<details>

  <summary><strong>Projects</strong></summary>

| Num | Name           | Branch              |
| --: | :------------- | :------------------ |
|   1 | Hello World UV | 0000-hello-world-uv |

</details>

## Pip Modules

- Update `pip`, `setuptools` and `wheel` to the latest versions:

  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  ```

## Project Structure

```
<project_name>
├── docs
├── src
│   └── <project_name>
│       └── __init__.py
├── tests
│   └── __init__.py
├── LICENSE.txt
├── README.md
└── pyproject.toml
```

## PyProject Template

```
[build-system]
requires = ["pip", "setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "hello-world-uv"
version = "0.0.1"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
license = {file = "LICENSE"}
keywords = []
authors = [
  { name = "your-name", email = "your-email" }
]
classifiers = [
  "Private :: Do not Upload",
  "Development Status :: 3 - Alpha",
  "Programming Language :: Python :: 3.12",
]
dependencies = []

# [project.scripts]

# [project.urls]

[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.basedpyright]
reportOptionalMemberAccess = "none"
typeCheckingMode = "standard"
```

## Project Setup Using [UV](https://github.com/astral-sh/uv)

- Create a new project

  ```powershell
  uv init <project-name>
  ```

- Initialize current project

  ```powershell
  cd <project directory>
  uv init
  ```

- Both of these commands will create this folder structure:

  ```
  <project-name>
  ├── .python-version
  ├── hello.py
  ├── pyproject.toml
  └── README.md
  ```

- Set project python version:

  ```powershell
  uv python pin <python-version>
  ```

- To create vitual environment, run below command. This will create a folder named `.venv`. ***Optional, uv will auto create virtual environment when adding packages***

  ```powershell
  uv venv
  ```

- Updated project folder structure after running `uv venv`.
  ```
  <project-name>
  ├── .venv
  ├── .python-version
  ├── hello.py
  ├── pyproject.toml
  └── README.md
  ```

- Create relevant files and folders. Ensure current working directory is set to `<project-name>`.

  ```powershell
  mkdir docs, src, tests
  touch LICENSE
  ```

- Add packages to project.

  ```powershell
  uv add <package>
  uv add --dev <package>
  ```

- Remove packages from project.

  ```powershell
  uv remove <package>
  uv remove --dev <package>
  ```

- To view installed packages, run below command.

  ```powershell
  uv pip list
  # or
  uv pip freeze
  ```

## Project Setup Using [Hatch](https://github.com/pypa/hatch)