# Quickstart: Examples & Contributor Workflow

This document explains how to execute the example scripts locally against the running container and manage the contributor recognition workflow.

## 1. Running the Examples

Ensure that the Wright Docker container is built and running:

```bash
# Verify the Docker containers are active
docker compose ps
```

### Pre-requisites

You must have Python 3.11+ installed locally. Install the required libraries:

```bash
pip install httpx
```

### Running the Quickstart Example

Navigate to the quickstart directory and run the script:

```bash
cd examples/quickstart
python main.py
```

### Running the Bracket Design Example

This script automates bracket design via the agent's CAD API:

```bash
cd examples/bracket-design
python main.py
```

Check the generated output:

```bash
ls output/
```

### Running the Bolt Analysis Example

Runs Bolt stress calculations:

```bash
cd examples/bolt-analysis
python main.py
```

---

## 2. All Contributors Workflow

The All Contributors CLI makes it easy to track and acknowledge contributions.

### Initializing and Adding Contributors

To add a new contributor, run the following npm commands:

```bash
# Add a contributor for coding contributions
npx all-contributors-cli add <github_username> code

# Add a contributor for documentation contributions
npx all-contributors-cli add <github_username> doc
```

### Generating the Contributor Table

Regenerate the table in the README:

```bash
npx all-contributors-cli generate
```
