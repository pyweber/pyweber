# Installing PyWeber

This guide covers the installation process for PyWeber and setting up your development environment.

## Requirements

PyWeber requires:

- Python 3.10 or higher
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

## Creating Your First Project

After installation, you can create a new PyWeber project:

```bash
# Create a new project
pyweber create-new my_project

# Create a project with configuration file
pyweber create-new my_project --with-config

# Navigate to the project directory
cd my_project

# Run the project
pyweber run
```

Visit `http://localhost:8800` in your browser to see your application.

## Configuration Management

PyWeber provides a robust configuration system to manage your application settings.

### Creating a Configuration File

You can create a configuration file for your project:

```bash
# Create a default config file in the .pyweber directory
pyweber create-config-file

# Specify a custom path and name
pyweber create-config-file --config-path config --config-name settings.toml
```

### Managing Configuration

PyWeber provides CLI tools to manage your configuration:

```bash
# Edit configuration interactively
pyweber --edit

# Add a new section to your configuration
pyweber add-section --section-name database
```

### Configuration Structure

The default configuration file includes these sections:

```toml
[app]
name = "my_project"
description = "A my_project built with pyweber framework"
version = "0.1.0"
debug = true

[server]
host = "127.0.0.1"
port = 8800
workers = 1

[session]
secret_key = "your-secret-key"
reload_mode = false
session_lifetime = 86400

[requirements]
packages = []
```

### Programmatic Configuration Access

You can access configuration values in your code:
```python
from pyweber.config.config import config

# Get configuration values
app_name = config.get("app", "name")
port = config.get("server", "port")

# Set configuration values
config.set("app", "version", "0.2.0")

# Delete configuration values
config.delete("app", "debug")
```

## Installing Project Requirements

PyWeber can install project dependencies defined in your configuration file:

```bash
# Install all packages listed in the requirements section
pyweber install

# Specify a custom config file path
pyweber install --config-file-path custom/path/config.toml
```

## Running Your Application

PyWeber provides multiple ways to run your application:

```bash
# Run with default settings
pyweber run

# Run a specific file
pyweber run app.py

# Run with hot reload enabled
pyweber run --reload

# Quick run with reload mode
pyweber --reload-mode
```

## Project Structure

A typical PyWeber project has the following structure:

```
my_project/
├── .pyweber/
│   └── config.toml      # Configuration file
├── main.py              # Application entry point
├── templates/
│   └── index.html       # HTML templates
└── src/
    ├── style/
    │   └── style.css    # CSS stylesheets
    └── assets/
        └── favicon.ico  # Static assets
```

## Updating PyWeber

To update PyWeber to the latest version:

```bash
pyweber --update
```

## Troubleshooting

If you encounter issues during installation or setup:

1. Ensure you're using Python 3.10 or higher
2. Check that pip is up to date: `pip install --upgrade pip`
3. Try installing in a virtual environment
4. For permission errors, use `pip install --user pyweber`

## Next Steps

Now that you have PyWeber installed, you can:

- Explore [Templates](template.md) for creating UI components
- Learn about [Elements](element.md) for DOM manipulation
- Understand [Events](events.md) for handling user interactions
- Set up routing with the [PyWeber class](router.md)

Happy coding with PyWeber!