# Contributing to Chunklet

First and foremost, thank you for considering contributing to Chunklet! We appreciate the time and effort you are willing to invest. Every contribution, whether it's a bug report, a new feature, or a documentation update, helps make Chunklet better for everyone.

## Getting Started

1.  **Fork the repository:** Click the "Fork" button at the top right of the [repository page](https://github.com/speedyk-005/chunklet).

2.  **Clone your fork:**

    ```bash
    git clone https://github.com/YOUR_USERNAME/chunklet.git
    cd chunklet
    ```

3.  **Install dependencies:** It is recommended to use a virtual environment.

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    pip install -e ".[dev]"
    ```

## Making Changes

1.  **Create a new branch:**

    ```bash
    git checkout -b my-feature-branch
    ```

2.  **Write your code:** Make your changes and ensure they follow the project's coding style.

3.  **Run tests:** Make sure all tests pass before submitting a pull request.

    ```bash
    pytest
    ```

4.  **Format your code:** This project uses `black` for code formatting. Please run it before committing your changes.

    ```bash
    black .
    ```

5.  **Lint your code:** This project uses `flake8` for linting. Please run it before committing your changes.

    ```bash
    flake8 src/ tests/
    ```

## Submitting a Pull Request

When you are ready to submit your pull request, please ensure you have done the following:

-   Provided a clear and descriptive title for your pull request.
-   Included a summary of the changes and why they are being made.
-   Referenced any related issues in the pull request description (e.g., "Fixes #123").
-   Confirmed that all tests pass.

## Code of Conduct

To ensure a welcoming and inclusive environment, we expect all contributors to adhere to our [Code of Conduct](#code-of-conduct).
