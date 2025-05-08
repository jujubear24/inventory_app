# Inventory Management System (Flask)

[![codecov](https://codecov.io/gh/jujubear24/inventory_app/graph/badge.svg?token=2THBYJRRBE)](https://codecov.io/gh/jujubear24/inventory_app)

This project is a Flask-based web application that provides a simple and efficient solution for managing product inventory. It addresses the challenges faced by small businesses in tracking stock levels, preventing stockouts, and generating reports.

## Features

* Product Management: Add, edit, and delete products.
* Inventory Tracking: Record stock level updates.
* Low-Stock Alerts: Receive notifications when stock levels are low.
* Reporting: Generate reports on inventory levels.
* User Authentication: Secure access to the application.

## Technologies Used

* **Backend Framework:** Flask
* **Database & ORM:** SQLAlchemy, SQLite, Alembic (for database migrations)
* **Templating:** Jinja2
* **Forms:** Flask-WTF, WTForms
* **Authentication:** Flask-Login (session-based), Flask-Dance (for OAuth, if applicable)
* **Environment Management:** python-dotenv
* **Frontend:** HTML, CSS. TailWind CSS (optional)
* **Package Management:** uv
* **Testing:** pytest, pytest-cov, pytest-flask, pytest-mock
* **CI/CD:** GitHub Actions

## Getting Started

1. Clone the repository:

    ```bash
    git clone <repository_url>
    ```

2. Navigate to the project directory:

    ```bash
    cd inventory_app 
    ```

3. Create and activate a virtual environment using `uv`:

    ```bash
    uv venv .venv
    source .venv/bin/activate
    ```

    (On Windows, use: `.venv\Scripts\activate`)
4. Install dependencies (this installs core and development dependencies from `pyproject.toml`):

    ```bash
    uv pip install .[dev]
    ```

5. **Environment Variables:** Create a `.env` file in the project root by copying the `.env.example` (if you provide one) or by creating it manually. This file will be used by `python-dotenv` to load environment variables like `SECRET_KEY`, `DATABASE_URL`, etc.
    Example `.env` content:

    ```env
    FLASK_APP=app:create_app() # Or your actual app factory/instance
    FLASK_DEBUG=True
    SECRET_KEY='your_very_secret_key_here'
    DATABASE_URL='sqlite:///./instance/inventory.db' 
    # Add other OAuth credentials if using Flask-Dance
    # GITHUB_OAUTH_CLIENT_ID=your_client_id
    # GITHUB_OAUTH_CLIENT_SECRET=your_client_secret
    ```

6. Initialize and migrate the database using Alembic (driven by Flask-Migrate):

    ```bash
    # If setting up for the first time and migrations folder doesn't exist:
    # flask db init 
    # Then, or if migrations folder already exists:
    flask db migrate -m "Initial database setup or descriptive message for new migration"
    flask db upgrade
    ```

7. Run the application:

    ```bash
    flask run
    ```

    The application should now be running on `http://127.0.0.1:5000/`.

## Development Workflow & CI/CD

This project utilizes a Git workflow and CI/CD automation to ensure code quality, consistency, and a streamlined development process.

### A. Git Branching Strategy

We follow a simple branching model:

* **`main` branch:**
  * This is a **protected branch**.
  * It represents the most stable, production-ready (or latest releasable) version of the project.
  * All changes are merged into `main` **only** through Pull Requests (PRs) from the `dev` branch.
  * Direct pushes to `main` are disallowed.

* **`dev` branch:**
  * This is the primary development integration branch.
  * All new features, bug fixes, and development work are committed directly to the `dev` branch.
  * Once `dev` has accumulated a set of completed and tested features and is considered stable, a Pull Request is created from `dev` to `main` for review and merging.

### B. CI/CD Automation (GitHub Actions)

We leverage GitHub Actions for Continuous Integration and Continuous Delivery automation.

1. **Pull Request (PR) Workflow (`.github/workflows/test.yml`)**:
    * When a Pull Request is opened or updated targeting the `main` branch (typically from `dev`), our primary CI workflow (`test.yml`) is automatically triggered.
    * This workflow performs the following critical checks:
        * Sets up the specified Python environment.
        * Installs project dependencies (using `uv` for speed).
        * Runs linters to enforce code style and catch potential issues.
        * Executes the complete automated test suite (e.g., using `pytest`), including unit and integration tests.
        * Generates and uploads code coverage reports (e.g., to Codecov).
    * **Branch protection rules** on `main` require all these status checks to pass successfully before the PR is eligible for merging.
    * (Optional: If auto-merge is enabled on the PR, it will merge automatically once all checks pass and other conditions are met.)

2. **Post-Merge Workflow (`.github/workflows/cycle-dev-branch.yml`)**:
    * After a Pull Request from `dev` is successfully merged into `main`, the `cycle-dev-branch.yml` workflow is automatically triggered.
    * This workflow's key responsibilities are:
        * To delete the old remote `dev` branch.
        * To recreate a fresh `dev` branch directly from the latest commit on `main`.
    * **Benefit**: This automation ensures that the `dev` branch always starts from the most recent stable baseline (`main`), minimizing branch drift, simplifying future integrations, and maintaining a clean development environment.

### C. Local Development Synchronization

After the CI/CD pipeline has successfully merged changes into `main` and recreated the remote `dev` branch, your local development environment needs to be synchronized with these remote updates.

* **Why it's needed**: Your local `main` and `dev` branches will be outdated. The local `dev` branch, in particular, will not reflect the newly reset remote `dev` branch.
* **Solution**:
  * **Primary Method (Script):** This project provides a shell script, `scripts/sync-local-dev.sh` (assuming this is its location and it's executable), to automate the necessary local Git commands. This script is version-controlled with the project.
  * **Optional Convenience (Git Alias):** For quicker access, you can set up a Git alias (e.g., `sync-local-dev`) on your local machine that executes the core synchronization commands or calls the provided script.

  * **What the script/alias does**:
        1. Ensures you are not on the `dev` branch, then switches to your local `main` branch and pulls the latest changes from `origin/main`.
        2. Fetches all updates from the remote repository (`origin`) and prunes any stale remote-tracking branches.
        3. Deletes your old local `dev` branch.
        4. Creates a new local `dev` branch that tracks the fresh `origin/dev` (which is now identical to the latest `main`).
        5. Switches your working directory to the new `dev` branch.

  * **How to use**:
        After a PR has been merged on GitHub and you've confirmed the `cycle-dev-branch.yml` workflow has completed successfully:
    * **Using the script** (assuming it's in `scripts/sync-local-dev.sh` and executable):

        ```bash
        sh ./scripts/sync-local-dev.sh 
        ```

    * **Using an optional alias** (if you have one configured locally):

        ```bash
        git sync-local-dev 
        ```

        *(Note: If you wish to create a local Git alias for convenience, you can configure it in your `~/.gitconfig` to either call the `scripts/sync-local-dev.sh` script or embed the synchronization commands directly.)*

---

### Running Tests Locally

Before pushing changes or creating a Pull Request, it's highly recommended to run the test suite locally to catch issues early:

```bash
# Example command, adjust based on your project's test runner
uv run pytest --cov=app --cov-branch --cov-report=xml:coverage.xml
```

## Author

[Jules Bahanyi](https://github.com/jujubear24)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
