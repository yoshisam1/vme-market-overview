# How to run
1. Create virtual environment ```bash python -m venv praisonai-env && source praisonai-env/bin/activate```
2. Install packages in requirements.txt
3. type ```bash python main.py```

# STRUCTURE
app.py will be the finish product' driver

backend directory will be for our agents, each agent should have its own directory
frontend directory will be for streamlit' development (later stage)

# DEPENDENCIES
To install all the dependencies required for this project, run the following command in your virtual environment:

```bash
pip install -r requirements.txt
```

This command will install all the packages listed in the requirements.txt file, which includes all the necessary packages and their versions for this project.

# ISSUES
Currently sequential processing snowballs previous responses and thus eventually hit token limit (and too long anyways)
Async implementation using PraisonAI framework only allows 10 concurrent agents

# TO TRY NEXT
Solution 1:
Either we process each page per API call (outside of PraisonAI) and store in a temp file, then the summarizer reads from it

Solution 2:
Find a way to work with async (PraisonAI limit is 10 agents)
Some libraries outside of PraisonAI might be able to help

(lets keep exploring solutions too!)