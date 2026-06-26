# Quickstart: Fix Test Validation Failures

1. Ensure dependencies are synchronized.

   ```powershell
   uv sync --all-packages --all-groups
   npm ci
   ```

2. Run the frontend unit tests.

   ```powershell
   npm run test --workspace=apps/web
   ```

3. Run both web build targets.

   ```powershell
   npm run build --workspace=apps/web
   npm run build:desktop --workspace=apps/web
   ```

4. Run Python tests.

   ```powershell
   uv run pytest
   ```

5. Confirm `git status --short --branch` shows only intentional bugfix changes before commit.
