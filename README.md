# Enhanced Calculator Command-Line Application

An enterprise-grade, extensible command-line calculator built with Python. The application implements standard and advanced arithmetic operations, history management with state restoration (Undo/Redo), an automated Observer-driven logging and persistence system, an interactive Read-Eval-Print Loop (REPL) interface, and continuous integration with strict test coverage enforcement.

---

## 📑 Table of Contents

1. [Project Overview](#-project-overview)
2. [Architecture & Design Patterns](#-architecture--design-patterns)
3. [Directory Layout](#-directory-layout)
4. [Installation & Setup](#-installation--setup)
5. [Configuration (.env)](#-configuration-env)
6. [Usage Guide (REPL)](#-usage-guide-repl)
7. [Unit Testing & Coverage](#-unit-testing--coverage)
8. [Continuous Integration (CI/CD)](#-continuous-integration-cicd)
9. [Error Handling & Logging](#-error-handling--logging)

---

## 🚀 Project Overview

This project delivers a robust, test-driven command-line calculator adhering to clean architecture and software engineering principles:

- **Comprehensive Arithmetic**: Standard operations (`add`, `subtract`, `multiply`, `divide`) alongside advanced calculations (`power`, nth `root`, `modulus`, `int_divide`, `percent`, `absolute_diff`).
- **State Management**: Full Undo and Redo capabilities powered by historical snapshots.
- **Automated Side-Effects**: Automatic logging and CSV persistence triggered transparently on every calculation.
- **Industrial Code Quality**: $\ge 90\%$ test coverage enforced by automated CI pipelines, robust input bounds validation, and custom domain exceptions.
- **Enhanced UX (Optional Features)**: ANSI color-coded REPL outputs (`colorama`) and dynamic command discovery powered by decorators.

---

## 🏛️ Architecture & Design Patterns

The architecture enforces loose coupling and high cohesion using classic object-oriented design patterns:

### 1. Factory Pattern (`app/operations.py`)

`OperationFactory` manages the registration and instantiation of mathematical operations adhering to the `Operation` abstract base class. Operations accept numerical operands (using `Decimal` for precise arithmetic) and isolate domain-specific errors (e.g., zero denominators, even roots of negative numbers).

### 2. Memento Pattern (`app/calculator_memento.py`, `app/history.py`)

Encapsulates historical state snapshots in `CalculatorMemento` objects. `HistoryManager` maintains an undo and redo stack, permitting restoration of prior calculation states without violating object encapsulation.

### 3. Observer Pattern (`app/calculator.py`)

Implements an event-driven publish-subscribe model via `CalculationObserver`. Observers automatically react whenever `Calculator.compute()` completes:

- **`LoggingObserver`**: Logs timestamped calculation details to the configured log file.
- **`AutoSaveObserver`**: Automatically exports session history to a CSV file using `pandas`.

### 4. Decorator Pattern (`main.py` - Advanced Feature)

Dynamically registers CLI control commands via `@CommandRegistry.register(name, description)`. This enables dynamic construction of the REPL help menu without hardcoding conditional branching.

### 5. Color-Coded Interface (`colorama` - Advanced Feature)

Standardizes terminal output formatting across errors (red), instructions and system status (yellow/cyan), prompt markers (blue), and successful evaluations (green).

---

## 📁 Directory Layout

```text
project_root/
├── app/
│   ├── __init__.py              # Package marker
│   ├── calculation.py           # Calculation record model and dict serialization
│   ├── calculator_config.py     # Environment variable loader (.env)
│   ├── calculator_memento.py    # Snapshot memento for undo/redo
│   ├── calculator.py            # Primary Calculator facade and Observer manager
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── history.py               # History management, Memento stacks, pandas persistence
│   ├── input_validators.py      # Input parsing and numerical range validation
│   ├── logger.py                # Logging system configuration
│   └── operations.py            # Operation base class, math classes, OperationFactory
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and isolated temporary directories
│   ├── test_calculation.py      # Serialization and representation tests
│   ├── test_calculator.py       # Facade integration, Observer dispatch, and validation tests
│   ├── test_history.py          # Undo/redo stack and pandas CSV persistence tests
│   └── test_operations.py       # Parameterized tests for operations and edge cases
├── .github/
│   └── workflows/
│       └── python-app.yml       # GitHub Actions CI workflow (90% test coverage gate)
├── .env                         # Local runtime environment configuration
├── .gitignore                   # Ignored files (venv, __pycache__, logs, data)
├── main.py                      # Interactive CLI entrypoint
├── README.md                    # Project documentation
└── requirements.txt             # Project runtime and development dependencies
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Git

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <REPOSITORY_NAME>
```

### 2. Create and Activate a Virtual Environment

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Required Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔧 Configuration (`.env`)

The application loads environment variables using `python-dotenv`. Default configurations are pre-defined in `app/calculator_config.py` and can be customized via `.env`:

```env
# ==========================================
# Calculator Configuration Settings
# ==========================================

# Base Directories & File Storage
CALCULATOR_LOG_DIR=logs
CALCULATOR_LOG_FILE=logs/calculator.log
CALCULATOR_HISTORY_DIR=data
CALCULATOR_HISTORY_FILE=data/history.csv

# History & State Settings
CALCULATOR_MAX_HISTORY_SIZE=100
CALCULATOR_AUTO_SAVE=true

# Calculation & Parsing Settings
CALCULATOR_PRECISION=4
CALCULATOR_MAX_INPUT_VALUE=1000000000
CALCULATOR_DEFAULT_ENCODING=utf-8
```

| Variable                      | Type    | Default               | Description                                                |
| ----------------------------- | ------- | --------------------- | ---------------------------------------------------------- |
| `CALCULATOR_LOG_DIR`          | String  | `logs`                | Directory path where application logs are stored           |
| `CALCULATOR_LOG_FILE`         | String  | `logs/calculator.log` | Path to the active application log file                    |
| `CALCULATOR_HISTORY_DIR`      | String  | `data`                | Directory path where CSV history exports reside            |
| `CALCULATOR_HISTORY_FILE`     | String  | `data/history.csv`    | Path to the default CSV persistence file                   |
| `CALCULATOR_MAX_HISTORY_SIZE` | Integer | `100`                 | Maximum calculation records retained in memory             |
| `CALCULATOR_AUTO_SAVE`        | Boolean | `true`                | Automatically export history to CSV after each calculation |
| `CALCULATOR_PRECISION`        | Integer | `4`                   | Decimal places for rounding calculation outputs            |
| `CALCULATOR_MAX_INPUT_VALUE`  | Float   | `1000000000`          | Maximum allowed numerical input magnitude                  |
| `CALCULATOR_DEFAULT_ENCODING` | String  | `utf-8`               | Default encoding for file operations                       |

---

## 💻 Usage Guide (REPL)

Start the interactive CLI:

```bash
python main.py
```

### Supported Arithmetic Operations

Format: `<operation> <operand_a> <operand_b>`

| Command         | Math Notation                | Example              | Description                      |
| --------------- | ---------------------------- | -------------------- | -------------------------------- |
| `add`           | $a + b$                      | `add 5 3`            | Addition                         |
| `subtract`      | $a - b$                      | `subtract 10 4`      | Subtraction                      |
| `multiply`      | $a \times b$                 | `multiply 6 7`       | Multiplication                   |
| `divide`        | $a / b$                      | `divide 20 4`        | Floating-point division          |
| `power`         | $a^b$                        | `power 2 3`          | Exponentiation                   |
| `root`          | $\sqrt[b]{a}$                | `root 27 3`          | Nth root calculation             |
| `modulus`       | $a \pmod b$                  | `modulus 10 3`       | Modulo remainder                 |
| `int_divide`    | $a \mathbin{/\mkern-6mu/} b$ | `int_divide 11 3`    | Integer floor division           |
| `percent`       | $\frac{a}{b} \times 100$     | `percent 25 100`     | Percentage of $a$ over $b$       |
| `absolute_diff` | $\|a - b\|$                  | `absolute_diff 4 10` | Absolute non-negative difference |

### Control Commands

- `history`: Display all calculation records currently held in memory.
- `clear`: Clear the active in-memory calculation history.
- `undo`: Revert the state to prior to the most recent operation.
- `redo`: Reapply the most recently reverted calculation.
- `save`: Manually serialize active history to the configured CSV file via `pandas`.
- `load`: Deserialize calculation records from the CSV file back into history.
- `help`: Dynamically display available arithmetic operations and commands.
- `exit`: Safely terminate the REPL session.

---

## 🧪 Unit Testing & Coverage

Testing is implemented using `pytest` and code coverage is evaluated via `pytest-cov`. The test suite targets edge cases such as division by zero, root of negative numbers, input validation boundaries, and malformed CSV recovery.

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage Enforcement ($\ge 90\%$)

```bash
pytest --cov=app --cov-fail-under=90 --cov-report=term-missing
```

---

## 🔄 Continuous Integration (CI/CD)

The GitHub Actions workflow is defined in `.github/workflows/python-app.yml`:

- **Triggers**: Executed on every `push` and `pull_request` targeting the `main` branch.
- **Environment**: Runs on `ubuntu-latest` with Python 3.11.
- **Dependencies**: Automatically installs packages from `requirements.txt`.
- **Quality Gate**: Runs `pytest --cov=app --cov-fail-under=90`. Any test failure or drop below $90\%$ code coverage fails the pipeline.

---

## 🛡️ Error Handling & Logging

- **Custom Exception Hierarchy**: `CalculatorError` acts as the base exception, specialized into `ValidationError` (for unparseable or out-of-range inputs) and `OperationError` (for mathematical domain errors).
- **Logging System**: Structured logs are written to `CALCULATOR_LOG_FILE` with severity levels (`INFO`, `WARNING`, `ERROR`), capturing operational events, operand parameters, and tracebacks without exposing internal crashes to the REPL.
