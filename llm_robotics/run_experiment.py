from openai import OpenAI
from mistralai.client import MistralClient
import sys
import numpy as np
import time
from llm_robotics.gpsr import GPSR
from llm_robotics.simulation import Simulation, FetchAndCount, DistributeApples, DistributeFruit, SimpleFetch
from llm_robotics.simulation import TestSimpleFetch, TestFetchAndCount, TestDistributeTableware, TestDistributeBottles

# is n=50 good?
# track statistics

class ExperimentManager:
    
    def __init__(self) -> None:
        pass
    
    
    
    def run_experiment(self,
                       client,
                       model,
                       simulation, 
                       chain_of_thought_mode, 
                       cot_frequency,
                       include_example,
                       selective_functions,
                       temperature, index, include_state=False,
                       max_queries = 40,
                       config_dict={}):
        
        robot = simulation(index)
        print(robot.task)
        print(robot.items_by_location)
        
        cfg = config_dict
        cfg["client"] = client
        cfg["model"] = model
        cfg["cot_mode"] = chain_of_thought_mode
        cfg["cot_frequency"] = cot_frequency
        cfg["max_queries"] = max_queries
        if isinstance(client, MistralClient):
            temperature = temperature / 2
        cfg["temperature"] = temperature
        cfg["selective_functions"] = selective_functions
        cfg["debug_mode"] = True
        cfg["color_print"] = False
        cfg["include_example"] = include_example
        cfg["include_state"] = include_state

        cfg["use_speech_recognition"] = True
        cfg["color_print"] = True
        cfg["debug_mode"] = False
        cfg["verbose_robot"] = True
        cfg["task_mode"] = "single"
        
        experiment = GPSR(robot, cfg, task=robot.task)
        llm_history = experiment.llm_history
        
        
            
        print(f"model: {cfg['model']}")
        print(f"temperature {temperature}")
        print(robot.items_by_location)
        print(robot.arms)
        print(robot.check_success())
        print(f"length: {len(llm_history)}")
        print(f"function calls: {experiment.number_of_function_calls}")
        return robot.check_success(), llm_history, experiment.number_of_function_calls
    
    
    
    def run_and_log_experiment(self, config_dict):

        experiments_range = config_dict["seeds"]
        simulation = config_dict["simulated_task"]

        max_queries = config_dict["max_queries"]
        cot_frequency = config_dict["cot_frequency"]
        chain_of_thought_mode = config_dict["cot_mode"]

        include_state = config_dict["include_state"]
        include_example = config_dict["include_example"]
        selective_functions = config_dict["selective_functions"]

        temperature = config_dict["temperature"]
        model = config_dict["model"]
        api_key = config_dict["api_key"]

        path = config_dict["path"]

        if "gpt" in model:
            client = OpenAI(api_key = api_key) 
        if "mistral" in model:
            client = MistralClient(api_key= api_key)


        print(f"Starting experiments\n{path}\n")
        with open(f"{path}/meta.txt", "a") as meta_file:
            print("success, length, time, number of function calls", file=meta_file)
            success_array = []
            length_array = []
            time_array = []
            num_fc_array = []
            for i in experiments_range:
                # Open a file for writing
                print(f"Starting experiment: {i}")
                start_time = time.time()
                with open(f'{path}/{i}.txt', 'w') as file:
                    # Save the current standard output (console)
                    original_stdout = sys.stdout

                    # Redirect the standard output to the file
                    sys.stdout = file

                    # Now, run experiment while printing to file
                    success, history, n = self.run_experiment(  client=client, model=model,
                                                                simulation=simulation,
                                                                chain_of_thought_mode=chain_of_thought_mode,
                                                                cot_frequency=cot_frequency,
                                                                include_example=include_example,
                                                                selective_functions=selective_functions,
                                                                temperature=temperature, index=i, include_state=include_state,
                                                                max_queries=max_queries,
                                                                config_dict=config_dict)
                    
                    # Restore the original standard output
                    sys.stdout = original_stdout
                end_time = time.time()
                execution_time = end_time - start_time
                print(f"finished experiment; success: {success}; length {len(history)}; time {execution_time:.2f}; function calls {n}\n")
                print(f"{success}, {len(history)}, {execution_time:.2f}, {n},", file=meta_file)
                success_array.append(success)
                length_array.append(len(history))
                time_array.append(execution_time)
                num_fc_array.append(n)
                
            success_array = np.array(success_array)
            length_array = np.array(length_array)
            time_array = np.array(time_array)
            num_fc_array = np.array(num_fc_array)
            print("----------", file=meta_file)
            print(f"Success avg: {np.mean(success_array)}", file=meta_file)
            print(f"Length avg: {np.mean(length_array)}; std: {np.std(length_array)}", file=meta_file)
            print(f"Time avg: {np.mean(time_array)}; std: {np.std(time_array)}", file=meta_file)
            print(f"Function calls avg: {np.mean(num_fc_array)}; std: {np.std(num_fc_array)}", file=meta_file)
            print("----------", file=meta_file)

