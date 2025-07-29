# Prompt

The `Prompt` class represents the result of a browser prompt dialog, containing both the user's input and the dialog identifier.

## Prompt Class

### Constructor
```python
def __init__(self, prompt_result: str, prompt_id: str):
```

**Parameters:**
- `prompt_result`: User's input from the prompt dialog
- `prompt_id`: Unique identifier for the prompt dialog

### Properties

#### `result`
The user's input from the prompt dialog.
- Contains the text entered by the user
- May be empty string if user entered nothing
- `None` if user cancelled the dialog

#### `id`
Unique identifier for the prompt dialog.
- Used to match responses with specific prompt requests
- Generated as UUID when dialog is created

### Magic Methods

#### `__repr__()`
Returns a string representation of the prompt result.

**Format:** `result={result}, id={id}`

## Usage Example

```python
from pyweber.models.window import Prompt

# Create prompt result (typically done internally)
prompt_result = Prompt(
    prompt_result="John Doe",
    prompt_id="550e8400-e29b-41d4-a716-446655440000"
)

# Access properties
print(prompt_result.result)  # "John Doe"
print(prompt_result.id)      # "550e8400-e29b-41d4-a716-446655440000"

# String representation
print(prompt_result)         # result=John Doe, id=550e8400-e29b-41d4-a716-446655440000

# Check user input
if prompt_result.result:
    print(f"User entered: {prompt_result.result}")
else:
    print("User cancelled or entered nothing")
```

## Integration with Window

The Prompt class is typically used with the Window.prompt() method:

```python
# In an async context
async def get_user_name():
    # Show prompt dialog with default value
    prompt_result = await window.prompt("Enter your name:", default="Anonymous")

    # Check user input
    if prompt_result.result:
        name = prompt_result.result
        print(f"Hello, {name}! (prompt ID: {prompt_result.id})")
        return name
    else:
        print(f"No name provided (prompt ID: {prompt_result.id})")
        return None

async def get_configuration():
    # Multiple prompts for configuration
    host = await window.prompt("Enter server host:", default="localhost")
    port = await window.prompt("Enter port number:", default="8080")

    if host.result and port.result:
        config = {
            "host": host.result,
            "port": int(port.result),
            "host_prompt_id": host.id,
            "port_prompt_id": port.id
        }
        return config
    else:
        return None
```

## Result Values

### Standard Values
- **String**: User's text input
- **Empty string**: User clicked OK without entering text
- **None**: User cancelled the dialog or dialog timed out

### Input Validation
```python
async def get_valid_email():
    while True:
        email_prompt = await window.prompt("Enter your email address:")

        if not email_prompt.result:
            return None  # User cancelled

        email = email_prompt.result.strip()
        if "@" in email and "." in email:
            return email
        else:
            await window.alert("Please enter a valid email address")
```

## Dialog Identification

### Purpose of ID
- Matches responses to specific prompt requests
- Enables handling multiple simultaneous prompts
- Provides audit trail for user interactions
- Useful for debugging and logging

### ID Generation
- Typically generated as UUID4 for uniqueness
- Created when prompt dialog is initiated
- Passed to client and returned with response

## Advanced Usage

### Form-like Input Collection
```python
async def collect_user_info():
    user_info = {}

    # Collect multiple pieces of information
    prompts = [
        ("name", "Enter your full name:", ""),
        ("email", "Enter your email:", ""),
        ("phone", "Enter your phone number:", ""),
    ]

    for field, message, default in prompts:
        result = await window.prompt(message, default=default)

        if not result.result:  # User cancelled
            return None

        user_info[field] = result.result
        user_info[f"{field}_prompt_id"] = result.id

    return user_info

# Usage
user_data = await collect_user_info()
if user_data:
    print(f"Collected: {user_data}")
```

### Timeout Handling
```python
async def get_input_with_timeout():
    try:
        result = await window.prompt("Enter value:", timeout=30)

        if result.result == "timeout":
            print("User didn't respond in time")
            return None
        elif result.result:
            return result.result
        else:
            print("User cancelled")
            return None

    except Exception as e:
        print(f"Prompt failed: {e}")
        return None
```

## Error Handling

### Input Validation
```python
async def get_numeric_input():
    while True:
        result = await window.prompt("Enter a number:")

        if not result.result:
            return None  # User cancelled

        try:
            number = float(result.result)
            return number
        except ValueError:
            await window.alert("Please enter a valid number")
```

### Cancellation Detection
```python
async def handle_prompt_cancellation():
    result = await window.prompt("Enter something:")

    if result.result is None:
        print("User cancelled the prompt")
    elif result.result == "":
        print("User entered empty string")
    else:
        print(f"User entered: {result.result}")
```

## Common Use Cases

1. **User Registration**: Collecting user information
2. **Configuration**: Getting settings from users
3. **Search Input**: Getting search terms or filters
4. **Quick Data Entry**: Simple form alternatives
5. **Authentication**: Getting passwords or tokens (not recommended for sensitive data)

## Browser Compatibility

Maps to JavaScript's `prompt()` dialog:
- `window.prompt("message", "default")` returns string or null
- PyWeber extends this with ID tracking and async support
- Maintains familiar prompt dialog UX

## Best Practices

### Message Design
```python
# Good: Clear, specific prompts
await window.prompt("Enter your username (3-20 characters):", default="user123")

# Avoid: Vague prompts
await window.prompt("Enter something:")
```

### Default Values
```python
# Provide helpful defaults
name = await window.prompt("Enter your name:", default="Anonymous")
port = await window.prompt("Enter port:", default="8080")
```

### Input Validation
```python
# Always validate user input
async def get_valid_port():
    while True:
        result = await window.prompt("Enter port (1-65535):", default="8080")

        if not result.result:
            return None

        try:
            port = int(result.result)
            if 1 <= port <= 65535:
                return port
            else:
                await window.alert("Port must be between 1 and 65535")
        except ValueError:
            await window.alert("Please enter a valid number")
```

## Security Considerations

- **Avoid for sensitive data**: Don't use for passwords or tokens
- **Validate all input**: Never trust user input without validation
- **Sanitize output**: Clean input before using in HTML or databases
- **Consider alternatives**: Use proper forms for complex input