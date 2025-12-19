# Installation

Ready to get Chunklet-py up and running? Fantastic! This guide will walk you through the installation process, making it as smooth as possible.

!!! info "Requirements"
    Chunklet-py requires **Python 3.9 or newer**. We recommend using Python 3.11+ for the best experience.

!!! note "Package Name Change"
    Chunklet-py was previously named `chunklet`. The old `chunklet` package is no longer maintained. When installing, make sure to use `chunklet-py` (with the hyphen) to get the latest version.
    
## The Easy Way

The most straightforward method to install Chunklet-py is by using `pip`:

```bash
# Install and verify version
pip install chunklet-py
chunklet --version
```

And that's all there is to it! You're now ready to start using Chunklet-py.

## Optional Dependencies

Chunklet-py offers optional dependencies to unlock additional functionalities, such as document processing or code chunking. You can install these extras using the following syntax:

*   **Document Processing:** For handling `.pdf`, `.docx`, `.epub`, and other document formats:
    ```bash
    pip install "chunklet-py[document]"
    ```
*   **Code Chunking:** For advanced code analysis and chunking features:
    ```bash
    pip install "chunklet-py[code]"
    ```
*   **Visualization:** For the interactive web-based chunk visualizer:
    ```bash
    pip install "chunklet-py[visualization]"
    ```
*   **All Extras:** To install all optional dependencies:
    ```bash
    pip install "chunklet-py[all]"
    ```

## The Alternative Way

For those who prefer to build from source, you can clone the repository and install it manually. This method allows for direct modification of the source code and installation of all optional features:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
pip install .[all]
```

But why would you want to do that? The easy way is so much easier.

## Contributing to Chunklet-py

Interested in helping make Chunklet-py even better? That's fantastic! Before you dive in, please take a moment to review our [**Contributing Guide**](https://github.com/speedyk-005/chunklet-py/blob/main/CONTRIBUTING.md). Here's how you can set up your development environment:

```bash
git clone https://github.com/speedyk-005/chunklet-py.git
cd chunklet-py
# For basic development (testing, linting)
pip install -e ".[dev]"
# For documentation development
pip install -e ".[docs]"
# For comprehensive development (including all optional features)
pip install -e ".[dev-all]"
```

These commands install Chunklet-py in "editable" mode, ensuring that any changes you make to the source code are immediately reflected. The `[dev]`, `[docs]`, and `[dev-all]` options include the necessary dependencies for specific development tasks.

Now, go forth and code! And remember, good developers always write tests. (Even in a Python project, we appreciate all forms of excellent code examples!)
