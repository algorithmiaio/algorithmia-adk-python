# Algorithm Development Kit (ADK), Python edition

```python
import Algorithmia
from adk import ADK


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def apply(input):
    return "hello {}".format(str(input))


algo = ADK(apply)
algo.serve("Algorithmia")
```

This document will describe the following:
- What is an Algorithm Development Kit
- Changes to Algorithm development
- Example workflows you can use to create your own Algorithms.


## What is an Algorithm Development Kit
An Algorithm Development Kit is a package that contains all of the necessary components to convert a regular application into one that can be executed and run on Algorithmia.
To do that, an ADK must be able to communicate with [langserver](https://github.com/algorithmiaio/langpacks/blob/develop/langpack_guide.md).
To keep things simple, an ADK exposes some optional functions, along with an `apply` function that acts as the explicit entrypoint into your algorithm.
Along with those basics, the ADK also exposes the ability to execute your algorithm locally, without `langserver`; which enables better debuggability.

![adk architecture](assets/adk_architecture.png)

This kit, when implemented by an algorithm developer - enables an easy way to get started with your project, along with well defined hooks to integrate with an existing project.


## Changes to Algorithm Development

Algorithm development does change with this introduction:
- Primary development file has been renamed to `src/Algorithm.py` to aide in understanding around what this file actually does / why it's important
- An additional import (`from adk import ADK`)
- An optional `load()` function that can be implemented
    - This enables a dedicated function for preparing your algorithm for runtime operations, such as model loading, configuration, etc
- A call to the handler function with your `apply` and optional` load` functions as inputs
    - ```python
      algo = ADK(apply)
      algo.serve("Algorithmia")
      ```
    - Converts the project into an executable, rather than a library
      - Which will interact with the `langserver` service on Algorithmia
      - But is debuggable via stdin/stdout when executed locally / outside of an Algorithm container
        - When a payload is provided to `serve()`, that payload will be directly provided to your algorithm when executed locally, bypassing stdin parsing and simplifying debugging!
      - This includes being able to step through your algorithm code in your IDE of choice! Just execute your `src/Algorithm.py` script and try stepping through your code with your favorite IDE

## Example workflows
Check out these examples to help you get started:
- [hello world example](examples/hello_world)
- [hello world example with loaded state](examples/loaded_state_hello_world)
- [pytorch based image classification](examples/pytorch_image_classification)
