# Python

A reference guide for Python.

<details>

  <summary><strong>Projects</strong></summary>

| Num | Name                     | Branch                        | Summary                                                                                                                  | Status |
| --: | :----------------------- | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------- | :----- |
|   1 | Hello World UV           | 0000-hello-world-uv           |                                                                                                                          | WIP    |
|   2 | OpenCV Video Splitter    | 0001-openv-video-splitter     | Use OpenCV to read video data, detect common patterns between each sections, and split the video into multiple sections. | WIP    |
|   3 | Selenium Tutorial Parser | 0002-selenium-tutorial-parser | Use selenium to parse tutorial page.                                                                                     | Idea   |
|   4 | Gitlab REST API          | 0003-gitlab-rest-api          | Use gitlab rest api to beautify information (issues, milestones, etc ...)                                                | WIP    |
|   5 | Debugger Adapter Protocol (DAP)          | 0004-DAP          | Learn how to utilize the Debugger Adapter Protocol (DAP)                                                | WIP    |

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
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
license = {file = "LICENSE"}
keywords = []
authors = [
  { name = "your-name", email = "your-email" }
]
classifiers = [
  "Private :: Do not Upload",
  "Development Status :: 3 - Alpha",
  "Programming Language :: Python :: 3.13",
]
dependencies = []

# [project.scripts]

# [project.urls]

[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.ruff]
indent-width = 4
line-length = 88

[tool.ruff.lint]
extend-select = ["ARG", "E", "F", "W"]
ignore = ["E501"]

[tool.basedpyright]
reportOptionalMemberAccess = "none"
reportUnusedImport = "none"
reportUnusedParameter = "none"
reportUnusedVariable = "none"
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

- To create vitual environment, run below command. This will create a folder named `.venv`. **_Optional, uv will auto create virtual environment when adding packages_**

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

- To install project as editable and from pyproject dependencies. Make sure current directory is at the root project directory.

  ```powershell
  uv pip install -e . -r pyproject.toml
  ```

- To sync project with updated pyproject.

  ```powershell
  uv sync
  ```

## Project Setup Using [Hatch](https://github.com/pypa/hatch)
