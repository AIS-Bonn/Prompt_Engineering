from llm_robotics.run_experiment import ExperimentManager
from llm_robotics.simulation import RandomConditional, RandomFetch, RandomEquals, RandomDistribute

config_dictionary = {

        # Insert your api key here and select the model you wish to use.
        # Possible models are GPT via the OpenAI API or Mistral via their API.
        "api_key": "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", # replace with your API key, this one is invalid
        "model": "gpt-3.5-turbo-0613", # alternative for mistral "mistral-large-latest"

        # Path to an existing directory to deposit the experiment transcripts.
        "path": "transcripts",

        # Maximum number of LLM tool calls processed before a task is forced to terminate.
        # Using a higher number can be costly if the LLM gets stuck in a loop.
        "max_queries": 40,

        # An iterable containing integers. The number of elements determines the number of samples.
        # Each integer will be used as the environment's seed in a single sample.
        # So range(0, 5) would create 5 samples with seeds of 0, 1,..., 4
        "seeds": range(0, 5),

        # Determines the task the LLM is meant to solve. Has to be a class from llm_robotics/simulation.py
        # The paper uses the four tasks RandomConditional, RandomFetch, RandomEquals, RandomDistribute
        # Random here indicates that the scenario will differ slightly based on an inserted seed
        "simulated_task": RandomFetch,
        
        # Determine whether or not to use Adaptive Functions
        "selective_functions": True,
        
        ## Determines the prompting style during the execution
        # None: Will not use any of the prompt engineering techniques
        # "once": Produce a single step-by-step plan at the start of the experiment
        # "repeated": Create a new step-by-step plan after a number of LLM tool calls according to cot_frequency
        # "ReAct": Use ReAct prompting during the experiment
        "cot_mode": None, # None, "once", "repeated", "ReAct"
        
        # Frequency with which to crate a new CoT plan
        "cot_frequency": 15,

        # Determines if an example is included in the prompt
        "include_example": False,

        # Determines if we want to include a State Description in the prompt
        "include_state": False,

        # Determines the temperature used by the LLM
        "temperature": 0,
    }


manager = ExperimentManager()
manager.run_and_log_experiment(config_dictionary)