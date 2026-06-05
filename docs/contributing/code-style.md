# Code Style & Quality Gates

To maintain a clean codebase and avoid quality regression, all commits must pass quality gate checks.

---

## 1. Python Style Guidelines

We use **Ruff** for linting and formatting Python packages.

### Rules Configuration
*   **Target Version**: Python 3.11+
*   **Linters Enabled**: `E` (Pycodestyle), `F` (Pyflakes), `I` (Isort), `UP` (Pyupgrade), `RUF` (Ruff-specific rules).
*   **Docstrings**: Maintain existing docstrings and comments. Focus on writing self-documenting code.

### Command Execution
```bash
# Verify code compliance
make lint

# Apply automatic formatting
make format
```

---

## 2. TypeScript / React Style Guidelines

We use **ESLint** for code analysis and **Prettier** for formatting React apps.

### Rules Configuration
*   **Framework**: React 19 (SPA)
*   **CSS Class Ordering**: Sort Tailwind classes logically if Tailwind is used.
*   **Formatting**: Standard double quotes for strings, 2-space indentation, semicolons enabled.

### Command Execution
```bash
# Format typescript assets
npx prettier --write apps/web/

# Run ESLint validations
make lint
```
