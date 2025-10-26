# Utils

This section provides an overview of the utility functions used in Chunklet. These functions handle tasks like language detection, file type checking, token counting, and input validation.




## `token_utils`
Provides a reliable way to count tokens while keeping an eye on performance with a built-in cache.

**Source Code:** [chunklet/utils/token_utils.py](https://github.com/speedyk-005/chunklet-py/blob/main/chunklet/utils/token_utils.py)

When Chunklet needs to keep an eye on token limits (which is often!), it turns to our `token_utils`. This little helper provides a super safe way to count tokens in your text, especially when you're using a custom token counter function. No more guessing games with your LLM context windows! Specifically, the `count_tokens` function is your go-to for getting an accurate token count. It wraps your custom token counter with robust error handling, ensuring that the returned value is always a reliable integer. To make things even more efficient, it's also cached, so you won't have to count the same text twice!

**Usage Example:**
```python
from chunklet.utils.token_utils import count_tokens
from chunklet.exceptions import CallbackExecutionError

# For demo purpose, lets use a split as token counter
def token_counter(text: str) -> int:
    if "fail" in text:
        raise ValueError("Intentional failure")
    return len(text.split())

print()
token_count = count_tokens("this is a valid text", token_counter)
print(f"Token count: {token_count}")

try:
    token_count = count_tokens("this shall fail", token_counter)
except CallbackExecutionError as e:
    print(f"Error in the token counting process: {e}")
```
<details>
<summary>Click to see output</summary>

```
Token count: 5

Error in the token counting process: Token counter failed while processing text starting with: 'this shall fail...'.
💡 Hint: Please ensure the token counter function handles all edge cases and returns an integer. 
Details: Intentional failure
```
</details>


## `validation`
A robust validation layer that uses Pydantic to ensure all your inputs are correct and properly formed.

**Source Code:** [chunklet/utils/validation.py](https://github.com/speedyk-005/chunklet-py/blob/main/chunklet/utils/validation.py)

Our `validation` utility is Chunklet's quality control department, ensuring that all inputs are up to snuff using the power of Pydantic. It's like having a super-strict but very helpful bouncer for your data! The `validate_input` decorator is a neat trick that uses a Pydantic `TypeAdapter` to validate function inputs, making sure everything is just right before processing. And for those times when you're dealing with collections, the `safely_count_iterable` function is your best friend. It not only counts the items in an iterable but also makes sure each item is exactly the type you expect, preventing any unexpected surprises down the line.

**Usage Example:**
```python
from chunklet.utils.validation import validated_input, safely_count_iterable
from chunklet.exceptions import InvalidInputError

# For automatic input validation based on type hint
@validated_input 
def greet(name: str, age: int):
    print(f"Hello {name}! You said you are {age}. Nice to meet you.")

greet("Bob", 33)

print()
try:
    greet(33, "12")
except InvalidInputError as e:
    print(f"Error while greeting: {e}")

# Now let's try counting an iterable with invalid type
print()
try:
    age = [18, 25, "not_an_age", 12]
    count = safely_count_iterable(age, name="age", item_types=(str,))
except InvalidInputError as e:
    print(f"Error while counting: {e}")
```
<details>
<summary>Click to see output</summary>

```
Hello Bob! You said you are 33. Nice to meet you.

Error while greeting: (name) Input should be a valid string.
Found: (input=33, type=int)

Error while counting: (age[0]) Input has an invalid item.
Found: (input=18, type=int).
💡 Hint: Ensure all elements in the iterable are:
['str']
```
</details>