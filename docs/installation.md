# Installing PyWeber

This guide covers the installation process for PyWeber and setting up your development environment.

## Requirements

PyWeber requires:

- Python 3.8 or higher
- pip (Python package installer)

## Standard Installation

The simplest way to install PyWeber is using pip:

```bash
pip install pyweber
```

This installs the latest stable version of PyWeber and all its dependencies.

## Development Installation

For the latest development version with the newest features (which may be less stable), install directly from GitHub:

```bash
pip install git+https://github.com/pyweber/pyweber.git
```

## Verifying Installation

Verify that PyWeber is installed correctly:

```bash
pyweber --version
```

This should display the current version of PyWeber.

## Dependencies

PyWeber automatically installs the following dependencies:

- lxml: For HTML parsing and template processing
- websockets: For real-time communication
- watchdog: For file monitoring and hot reload

## Virtual Environments

It's recommended to use a virtual environment for your PyWeber projects:

### Using venv (Python's built-in virtual environment)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install PyWeber in the virtual environment
pip install pyweber
```

### Using conda

```bash
# Create a conda environment
conda create -n pyweber-env python=3.10

# Activate the environment
conda activate pyweber-env

# Install PyWeber
pip install pyweber
```

## Creating Your First Project

After installation, you can create a new PyWeber project:

```bash
# Create a new project
pyweber create-new my_project

# Navigate to the project directory
cd my_project

# Run the project
pyweber run
```

Visit `http://localhost:8800` in your browser to see your application.

## Manual Project Setup

If you prefer to set up a project manually:

1. Create a project directory:
   ```bash
   mkdir my_project
   cd my_project
   ```

2. Create a minimal project structure:
   ```
   my_project/
   ├── main.py
   ├── templates/
   │   └── index.html
   └── src/
       ├── style/
       │   └── style.css
       └── assets/
           └── favicon.ico
   ```

3. Create a basic `main.py` file:

    ```python
    import pyweber as pw

    class HomePage(pw.Template):
        def __init__(self, app: pw.Router):
            super().__init__(template="index.html")

    def main(app: pw.Router):
        app.add_route("/", template=HomePage(app=app))

    if __name__ == "__main__":
        pw.run(target=main)
    ```

4. Create a simple `templates/index.html` file:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>My PyWeber App</title>
       <link rel="stylesheet" href="/src/style/style.css">
   </head>
   <body>
       <h1>Welcome to PyWeber!</h1>
       <p>This is a manually created project.</p>
   </body>
   </html>
   ```

5. Run your application:
   ```bash
   python main.py
   ```

## Troubleshooting

### Common Installation Issues

#### lxml Installation Problems

If you encounter issues installing lxml:

- **Windows**: You might need to install Visual C++ Build Abilities
- **Linux**: Install the development packages for libxml2 and libxslt
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libxml2-dev libxslt-dev
  
  # Fedora/CentOS
  sudo dnf install libxml2-devel libxslt-devel
  ```
- **macOS**: Install with Homebrew
  ```bash
  brew install libxml2
  ```

#### Permission Errors

If you encounter permission errors during installation:

```bash
# On Windows, run as administrator
# On macOS/Linux, use sudo
sudo pip install pyweber
```

Or install for the current user only:

```bash
pip install --user pyweber
```

#### Dependency Conflicts

If you encounter dependency conflicts:

```bash
pip install pyweber --upgrade --force-reinstall
```

#### Path Issues

If the `pyweber` command is not found after installation:

1. Ensure Python's scripts directory is in your PATH
2. Try using `python -m pyweber` instead

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/pyweber/pyweber/issues) for similar problems
2. Create a new issue with details about your environment and the error message
3. Refer to the [troubleshooting guide](troubleshooting.md) for more detailed solutions

## Next Steps

Now that you have PyWeber installed, you can:

- Follow the [Quick Start Guide](index.md#quick-start)
- Learn about the [CLI](cli.md)
- Explore [Templates](template.md)
- Set up [Routing](router.md)

Happy coding with PyWeber!