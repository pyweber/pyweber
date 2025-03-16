# PyWeber CLI

The PyWeber Command Line Interface (CLI) provides abilities to create, run, and manage PyWeber applications.

## Installation

The CLI is automatically installed with PyWeber:

```bash
pip install pyweber
```

## Available Commands

### Check Version

Display the current version of PyWeber.

```bash
pyweber --version
# or
pyweber -v
```

### Create a New Project

Create a new PyWeber project with the recommended directory structure.

```bash
pyweber create-new my_project
```

This command creates a new project with the following structure:

```
my_project/
├── .pyweber/
│   └── config.json
├── src/
│   ├── assets/
│   │   └── favicon.ico
│   └── style/
│       └── style.css
├── templates/
│   └── index.html
└── main.py
```

### Run a Project

Run a PyWeber application.

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

This updates the `.pyweber/config.json` file to set `reload_mode` to `true`.

### Update PyWeber

Update PyWeber to the latest version.

```bash
pyweber --update
# or
pyweber -u
```

## Configuration

When creating a new project, PyWeber generates a `.pyweber/config.json` file with default settings. This file contains configuration for:

- Application information
- Server settings
- WebSocket settings
- Session management
- And more

You can modify this file to customize your application's behavior.

## Project Structure

A typical PyWeber project includes:

- **main.py**: Entry point for your application
- **templates/**: HTML templates
- **src/style/**: CSS stylesheets
- **src/assets/**: Static assets like images and icons
- **.pyweber/**: Configuration files

## Example Usage

### Create and Run a Project

```bash
# Create a new project
pyweber create-new my_webapp

# Navigate to the project directory
cd my_webapp

# Run the application with hot reload
pyweber run --reload
```

### Custom Entry Point

If your main file is not named `main.py`:

```bash
pyweber run app.py --reload
```

## Troubleshooting

If you encounter issues with the CLI:

1. Ensure you have the latest version of PyWeber installed
2. Check that you're in the correct directory
3. Verify that your project structure follows PyWeber conventions
4. Check the console for error messages

---
For more detailed information, refer to the [PyWeber documentation](https://pyweber.readthedocs.io/).