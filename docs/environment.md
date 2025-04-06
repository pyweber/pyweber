# Environment Variables in PyWeber

PyWeber supports various environment variables that allow you to configure its behavior without modifying configuration files. This approach is particularly useful for deployment scenarios, containerized applications, or when you need to override configuration temporarily.

## Available Environment Variables

### Core Variables

| Variable Name | Type | Default | Description |
|---------------|------|---------|-------------|
| `PYWEBER_RELOAD_MODE` | Boolean | `False` | Enables or disables auto-reload functionality. When set to `True`, PyWeber will watch for file changes and automatically restart the application. Valid values: `True`, `False`, `1`, `0`, `yes`, `no` (case-insensitive). |

### Usage Examples

#### Command Line

```bash
# Enable reload mode
PYWEBER_RELOAD_MODE=True python main.py

# Disable reload mode
PYWEBER_RELOAD_MODE=False python main.py

#Automatically Enable using pyweber CLI
pyweber -r 

# or
pyweber run --reload
```

#### In Python Code
```python
import os
import pyweber as pw

# Set environment variable programmatically
os.environ['PYWEBER_RELOAD_MODE'] = 'True'

# Start PyWeber application
pw.run(target=main)
```
## Environment Variables vs. Configuration Files

PyWeber follows these precedence rules when determining configuration values:

1. Environment variables (highest priority)
2. Command-line arguments
3. Configuration file settings
4. Default values (lowest priority)

This means that environment variables will override any settings in your configuration files, allowing for flexible deployment configurations without modifying your codebase.

## Best Practices

- Use environment variables for deployment-specific configurations
- Use configuration files for application-specific settings
- Use environment variables for sensitive information (like API keys) instead of storing them in configuration files
- Document all environment variables used by your application for easier deployment and maintenance

## Future Environment Variables

As PyWeber evolves, additional environment variables will be added to provide more configuration options. Check this documentation for updates in future releases.