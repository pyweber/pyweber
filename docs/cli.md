# PyWeber CLI

The PyWeber Command Line Interface (CLI) provides tools to create, manage, and run PyWeber applications.

## Installation

The CLI is automatically installed with PyWeber:

```bash
pip install pyweber
```

## Basic Commands

### Check Version

Display the current version of PyWeber:

```bash
pyweber --version
# or
pyweber -v
```

### Update PyWeber

Update to the latest version of PyWeber:

```bash
pyweber --update
# or
pyweber -u
```

## Project Management

### Create a New Project

Create a new PyWeber project with the recommended directory structure:

```bash
pyweber create-new my_project
```

Add the `--with-config` flag to automatically create a configuration file:

```bash
pyweber create-new my_project --with-config
```

This command creates a new project with the following structure:

```
my_project/
├── src/
│   ├── assets/
│   │   └── favicon.ico
│   └── style/
│       └── style.css
├── templates/
│   └── index.html
└── main.py
```

If `--with-config` is specified, it also creates:

```
my_project/
├── .pyweber/
│   └── config.toml
```

### Run a Project

Run a PyWeber application:

```bash
pyweber run
```

By default, this command runs the `main.py` file in the current directory. You can specify a different file:

```bash
pyweber run app.py
```

#### Hot Reload

Enable hot reload during development to automatically refresh the browser when files change:

```bash
pyweber run --reload
```

You can also run with reload mode directly:

```bash
pyweber -r
```

This updates the configuration file to set `reload_mode` to `true`.

## Configuration Management

### Create Configuration File

Create a configuration file for an existing project:

```bash
pyweber create-config-file
```

You can specify a custom path and filename:

```bash
pyweber create-config-file --config-path .config --config-name settings.toml
```

### Edit Configuration

Edit the project configuration interactively:

```bash
pyweber -e
```

This opens an interactive menu where you can:
- Edit existing fields
- Remove fields
- Remove sections
- Add new fields
- Add new sections

### Add Configuration Section

Add a new section to the configuration file:

```bash
pyweber add-section --section-name database
```

## Dependency Management

### Install Requirements

Install project dependencies defined in the configuration file:

```bash
pyweber install
```

You can specify a custom configuration file path:

```bash
pyweber install --config-file-path custom/path/config.toml
```

## Configuration File Format

PyWeber uses TOML for configuration files. A typical configuration includes:

```toml
[app]
name = "My PyWeber App"
description = "A PyWeber application"
keywords = ["pyweber", "web", "python"]
icon = "src/assets/favicon.ico"

[server]
host = "localhost"
port = 8800

[session]
reload_mode = false

[websocket]
host = "localhost"
port = 8801

[requirements]
packages = ["requests", "pillow"]
```

## Configuration Types

When adding new configuration fields, you can specify types:

| Type | Format Example |
|------|----------------|
| String | `name str Alex` |
| Integer | `age int 18` |
| Float | `price float 19.99` |
| List | `tags list python flask api` |
| Dictionary | `db dict user:str=admin; port:int=5432` |

## Example Workflows

### Create and Run a New Project

```bash
# Create a new project with configuration
pyweber create-new my_webapp --with-config

# Navigate to the project directory
cd my_webapp

# Run the application with hot reload
pyweber run --reload
```

### Update Configuration and Install Dependencies

```bash
# Edit configuration interactively
pyweber -e

# Install project dependencies
pyweber install
```

### Customize Project Configuration

```bash
# Add a new database section
pyweber add-section --section-name database

# Edit configuration to add database settings
pyweber -e
```

## Troubleshooting

If you encounter issues with the CLI:

1. Ensure you have the latest version of PyWeber installed
2. Check that you're in the correct directory
3. Verify that your project structure follows PyWeber conventions
4. Check the console for error messages