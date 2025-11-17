# Python

A reference guide for Python.

<details>

  <summary><strong>Projects</strong></summary>

| Num | Name                            | Branch                        | Summary                                                                                                                  | Status |
| --: | :------------------------------ | :---------------------------- | :----------------------------------------------------------------------------------------------------------------------- | :----- |
|   0 | Hello World UV                  | 0000-hello-world-uv           |                                                                                                                          | WIP    |
|   1 | OpenCV Video Splitter           | 0001-openv-video-splitter     | Use OpenCV to read video data, detect common patterns between each sections, and split the video into multiple sections. | WIP    |
|   2 | Selenium Tutorial Parser        | 0002-selenium-tutorial-parser | Use selenium to parse tutorial page.                                                                                     | Idea   |
|   3 | Gitlab REST API                 | 0003-gitlab-rest-api          | Use gitlab rest api to beautify information (issues, milestones, etc ...)                                                | WIP    |
|   4 | Debugger Adapter Protocol (DAP) | 0004-DAP                      | Learn how to utilize the Debugger Adapter Protocol (DAP)                                                                 | WIP    |
|   5 | Text To Speech To Bin           | 0005-text-to-speech-to-bin    | Use text to speech to convert text to binary data.                                                                       | WIP    |
|   6 | Pytest Learn                    |                               |                                                                                                                          |        |
|   7 | Excel                           | 0007-excel                    |                                                                                                                          | WIP    |

</details>

## Git

### gitattributes

```powershell
Set-Content -Path ".gittattributes" -Value @("*.sh text eol=lf", "*.yml text eol=lf")
```

```bash
echo -e "*.sh text eol=lf\n*.yml text eol=lf\n" > .gitattributes
```

## UV

### Update UV

```bash
uv self update
```

### Tool

#### Install

- Install these tools so it can be used globally
  - ruff
  - black
  - isort

```bash
uv tool install ruff@latest --python 3.13.9
uv tool install basedpyright@latest --python 3.13.9
uv tool install debugpy@latest --python 3.13.9
uv tool install hererocks@latest --python 3.13.9
uv tool install git-cliff@latest --python 3.13.9
uv tool install yamlfix@latest --python 3.13.9
uv tool install refurb@latest --python 3.13.9
uv tool install shellcheck-py@latest --python 3.13.9
```

#### Uninstall

```bash
uv tool uninstall ruff basedpyright git-cliff yamlfix refurb
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

## Project Setup Using [UV](https://github.com/astral-sh/uv)

- Create a new project

  ```bash
  uv init <project-name>
  ```

- Initialize current project

  ```bash
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

  ```bash
  uv python pin <python-version>
  ```

- To create vitual environment, run below command. This will create a folder named `.venv`. **_Optional, uv will auto create virtual environment when adding packages_**

  ```bash
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

  ```bash
  mkdir docs, src, tests
  touch LICENSE
  ```

- Add dependency packages to project.

  ```bash
  uv add <package>
  uv add "<package>; sys_platform == 'linux'"
  uv add "<package>; python_version >= '3.11'"
  uv add "<package> >=7.1.0,<8; sys_platform == 'linux'; python_version < '3.10'"
  ```

- Add project optional dependency packages for extra features:

  ```bash
  uv add <package> --optional <feature>
  ```

- Add package to dependency group (usually for development purposes)

  ```bash
  uv add --group test pytest
  ```

- Remove packages from project.

  ```bash
  uv remove <package>
  uv remove --dev <package>
  ```

- To view installed packages, run below command.

  ```bash
  uv pip list
  # or
  uv pip freeze
  ```

- To install project as editable and from pyproject dependencies. Make sure current directory is at the root project directory.

  ```bash
  uv pip install -e . -r pyproject.toml
  ```

- To sync project with updated pyproject.

  ```bash
  uv sync
  uv sync --group <group-name>
  ```

## PyProject Template

```toml
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

[project.optional-dependencies]
dev = [
]

# for development only
[dependency-groups]
dev = [
  "pytest"
# "pytest-asyncio"
# "pytest-httpx",
# "coverage",
]

# [project.scripts]

# [project.urls]

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

## Keep In View

### Pyproject with build?

<details>

  <summary><strong>Pyproject with build?</strong></summary>

  ```toml
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

  [project.optional-dependencies]
  dev = [
    "pytest", # "pytest-asyncio"
    "pytest-httpx",
    "coverage",
    "refurb",
    "debugpy",
  ]

  # [project.scripts]

  # [project.urls]

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
  
</details>

### Pip Modules

<details>

  <summary><strong>Pip Modules</strong></summary>
  - Update `pip`, `setuptools` and `wheel` to the latest versions:

  ```bash
  python -m pip install --upgrade pip setuptools wheel
  ```

</details>

## Project Setup Using [Hatch](https://github.com/pypa/hatch)
