# Project Documentation 📄

## How to Run 🚀

1. **Create a Virtual Environment**
    ```bash
    python -m venv langgraph-env && source langgraph-env/bin/activate
    ```

2. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application**
    ```bash
    streamlit run app.py
    ```

4. **Provide a Prompt When prompted, include the file path and query. For example:**
    ```bash
    Hi, I am currently working on an industry analysis for the Lending industry. Please find the attached relevant report in path data/Source1.pdf . I am trying to give a general overview of both the Global and Indonesia lending market, with a slight tilt towards positive outlook. Can you help? Thanks.
    ```


## Project Structure 🗂️
```bash
project/
├── .streamlit/
│   ├── secrets.toml                # Where you should put the API keys
│   ├── secrets.toml.example        # Example on how to make the secrets.toml file
├── main.py                         # Entry point of the application
├── .gitignore                      # Things to ignore in git (dependencies, caches, etc.)
├── graph/
│   ├── __init__.py                 # Makes the directory a Python package
│   ├── nodes.py                    # Contains the node definitions (process_input, process_pdf  , etc.)
│   ├── state.py                    # Defines the `State` TypedDict and related shared structures
│   ├── parsers.py                  # Contains all Pydantic models and parsers
├── tools/
│   ├── __init__.py                 # Makes the directory a Python package
│   ├── tools.py                    # Contains the PDFPlumberTool logic
│   ├── llm.py                      # Contains LLM initialization logic (e.g., ChatOpenAI setup)
├── utils/
│   ├── __init__.py                 # Makes the directory a Python package
│   ├── logging.py                  # Utility functions for logging and debugging
│   ├── helpers.py                  # Any additional helper functions
├── queries.txt                     # Questions to test the box
└── requirements.txt                # Python dependencies
```

## Adding Nodes 🛠️
Nodes represent steps in the processing graph. To add a new node:

1. **Create the Node Function**
Add the new node in graph/nodes.py. Each node should accept and modify the shared State object
```python
async def my_new_node(state: State):
    # Logic here
    state["new_key"] = "new_value"
```

2. **Register the Node in main.py**
Update the graph in main.py
```python
graph_builder.add_node("my_new_node", my_new_node)
graph_builder.add_edge("previous_node", "my_new_node")
```

3. **Update State**
If the node adds new keys to the state, update State in graph/state.py to include them.

## Adding Tools 🧰
Tools are utilities or integrations (e.g., PDF parsing, LLM). To add a new tool:
1. **Create a tool in tools/tools.py**
```python
class MyTool:
    def process(self, data):
        # Tool logic here
        return processed_data
```

2. **Register the Tool**
Initialize the tool in tools/__init__.py:
```python
from .my_tool import MyTool

my_tool = MyTool()
```

3. **Use the Tool in Nodes**
Import and use the tool in node logic:
```python
from tools import my_tool

async def node_using_tool(state: State):
    result = my_tool.process(state["input_data"])
    state["result"] = result
```

## Using Structured Outputs 🧰
Structured output ensures that the responses from the LLM are consistent and follow a predefined schema, making it easier to process and validate data.

1. **Define the Structured Output**
Create a new Pydantic model in graph/parsers.py to define the structure of the output. Example: Adding a New Parser in parsers.py
```python
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from typing import List

class ExampleOutput(BaseModel):
    key_1: str = Field(description="Description for key_1.")
    key_2: int = Field(description="Description for key_2.")
    details: List[str] = Field(description="A list of details.")

# Create a parser for the model
example_output_parser = PydanticOutputParser(pydantic_object=ExampleOutput)
```

2. **Use the Parser in a Node**
In the node function (e.g., in graph/nodes.py), include the structured output format in the LLM's prompt. Example: Using the Parser in a Prompt
```python
from graph.parsers import example_output_parser

async def example_node(state: State):
    # Define the prompt
    prompt = (
        "You are an advanced assistant. Based on the input below, respond with structured data:\n\n"
        f"Input: {state['query']}\n\n"
        "Your response must follow this JSON format:\n"
        f"{example_output_parser.get_format_instructions()}"
    )

    # Call the LLM
    response = await llm.ainvoke([{"role": "user", "content": prompt}])

    # Parse the response
    try:
        parsed_output = example_output_parser.parse(response.content)
        # Update the state with the parsed output
        state["example_output"] = parsed_output.dict()
    except Exception as e:
        print(f"Error parsing structured output: {e}")
        raise ValueError("Invalid LLM response format.")
```

3. **Update the State**
If the new output needs to be part of the shared state, update the State definition in graph/state.py:
```python
from typing import TypedDict, List

class State(TypedDict):
    # Existing fields
    messages: List[dict]
    query: str
    example_output: dict  # Add the new field

```

## Changing the LLM Model 🤖
1. **Update the .env File**
The .env file contains the configuration for your OpenAI API key and default model. Update the OPENAI_API_KEY and add a new entry for the model:
```bash
# .env
OPENAI_API_KEY=your-openai-api-key
OTHER_PROVIDER_KEY=the-api-key
```

2. **Update the .env.example File**
To ensure other developers on your team know what environment variables are required, update the .env.example file to include the new OPENAI_MODEL variable.
```bash
# .env.example
OPENAI_API_KEY=your-openai-api-key
OTHER_PROVIDER_KEY=xxx
```

3. **Modify tools/llm.py**
Update the tools/llm.py file to read the OPENAI_MODEL variable from the .env file. Here’s an example llm.py:
```python
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Access API key and model from the environment
OTHER_PROVIDER_KEY = os.getenv("OTHER_PROVIDER_KEY")

# Initialize the LLM
llm = ChatOpenAI(model=THE_MODEL, api_key=OTHER_PROVIDER_KEY)
```
## Roadmap 🤖
- Use streamlit selection UI for sentiment choice
- Allow .docs/.doc/.docx format documents
- Enable faster inference & higher throughput (try other models and providers)
- Develop login features (to allow private use despite public link)

### Appendix/Resources
https://github.com/mkhorasani/Streamlit-Authenticator
https://github.com/GauriSP10/streamlit_login_auth_ui