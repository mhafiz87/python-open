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

## Tools Via UV

- Install these tools so it can be used globally
  - ruff
  - black
  - isort

```bash
uv tool install ruff@latest --python 3.13.9
uv tool install basedpyright@latest --python 3.13.9
uv tool install git-cliff@latest --python 3.13.9
uv tool install yamlfix@latest --python 3.13.9
uv tool install refurb@latest --python 3.13.9
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

- Useful packages to be included in development:

  ```powershell
  uv add --dev debugpy
  uv add --dev pytest
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

  ```powershell
  python -m pip install --upgrade pip setuptools wheel
  ```

</details>

## Project Setup Using [Hatch](https://github.com/pypa/hatch)
