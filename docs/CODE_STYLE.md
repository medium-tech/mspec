
## Code Style Guidelines

This project follows specific code style preferences to maintain consistency and readability:

### Quote Preferences
- **Single quotes** (`'`) for string literals
- **Triple double quotes** (`"""`) for docstrings only

```python
# Preferred
bl_label = 'My Node'
def my_function():
    """This is a docstring"""
    return 'result'

# Avoid
bl_label = "My Node"
def my_function():
    '''This is a docstring'''
    return "result"
```

**F string quotes**
```python

name = 'Brad'
data = {'age': 37}

# for simple f-strings: single quotes
greeting = f'Hello, {name}'

# for complex f-strings: 
#   double quotes to define the f-string, single quotes inside the f-string
msg = f"Brad is {data['age'] years old}"
```

### unused
- no unused imports
- no unused variables

### Section Headers

**Major sections** use hash borders:
```python
#
# section name
#
```

**Minor sections** use hash suffixes:
```python
# section name #
```

**Descriptive comments** are simple:
```python
# example explaining what is going on at this point in the code
```

### Whitespace
* 2 lines around major section headers and between classes
* 1 line around minor section headers and between functions
```python
import bpy


#
# value nodes
#


class MyValueNode(Node):
    """Node for handling values"""
    bl_label = 'Value Node'
    
    def init(self, context):
        # Create the output socket
        self.outputs.new('NodeSocketInt', 'value')


class MyOtherValueNode(Node):
    """Node for handling values"""
    bl_label = 'Value Node'
    
    def init(self, context):
        # Create the output socket
        self.outputs.new('NodeSocketInt', 'value')


# helper functions #

def create_default_value():
    # Return a sensible default
    return 42

def create_another_default_value():
    # Return a sensible default
    return 33


#
# registration
#


classes = [
    MyValueNode,
]
```

### Error handling
#### Fail early, fail loudly.

```python

# fails early with KeyError if x doesn't exist
x:int = data['x']

# fails later when we try to use None but expect int
x:int = data.get('x')
# we'll have a traceback unrelated to the fact that 
# x wasn't provided, making it harder to troubleshoot

# an exception to this rule is when we plan to use a default
x:int = data.get('x', 42)
```

#### Raise exceptions, don't exit
```python

# prefer exceptions because they provide tracebacks
try:
    do_something()
except:
    raise ValueError('Something bad happened')
    
# when we exit, we lose our traceback
try:
    do_something()
except:
    print('Something bad happened')
    sys.exit(1)

```
