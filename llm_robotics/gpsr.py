from llm_robotics.llm_manager import LLMManager
from llm_robotics.robot_interface import FunctionManager
from time import sleep
import pickle


SYSTEM_PROMPT_TEMPLATE = """
Imagine you are a helpful service robot in an apartment trying to assist the user. If the user asks you a question please answer it and if they give you a task you can call the various available tools and functions to execute work.
Never use more than one tool in a single response. 

<task_mode>

<chain_of_thought_mode>

The user is located at the parlor. If you want to interact with the user you have to go there first. Your current location is the parlor.
"""
SYSTEM_PROMPT_TEMPLATE = SYSTEM_PROMPT_TEMPLATE.strip("\n")

PROMPT_MODE_DICT = {
    "<chain_of_thought_mode>": {
        "once": "At the beginning of each task write a step-by-step guide for how you plan to achieve the task. Do not call a function during this first summary message.",
        "repeated": "Periodically write a step-by-step guide on how you plan to achieve the tasks.",
        "ReAct": "Alternate between messages which only explain the reasoning for the next function call and messages calling the functions.",
        "combined": "Outline a step-by-step plan for task completion in the and explain your reasoning before each function call.",
        None: "",
    },
    "<task_mode>": {
        "single": "After you have finished the task call the exit function.",
        "repeated": "If you have finished a task go back to the user and ask for another task.",
    },
}


class GPSR:
    
    def assemble_system_prompt(self, cot_mode=None, task_mode="single", example = False):
        llm = self.llm
        system_prompt = SYSTEM_PROMPT_TEMPLATE
        
        key = "<chain_of_thought_mode>"
        dict = PROMPT_MODE_DICT[key]
        system_prompt = system_prompt.replace(key, dict[cot_mode])
        
        key = "<task_mode>"
        dict = PROMPT_MODE_DICT[key]
        system_prompt = system_prompt.replace(key, dict[task_mode])
        
        system_prompt = system_prompt.replace("\n\n\n\n", "\n\n")
        
        if example:
            system_prompt += "\n\nTo help you, the following shows the execution of an example task."
            llm.create_message("system", system_prompt)
            self.add_example(cot_mode=cot_mode)
        else:
            llm.create_message("system", system_prompt)

            
    
    def add_example(self, cot_mode=None):
        llm = self.llm
        
        user_task = {
            "role": "user",
            "content": "Please bring me pens until there are 3 pens here."
        }
        
        cot = {
            "role": "assistant",
            "content": "To accomplish the task the following steps are needed:\n\n1. Count the number of pens in the parlor.\n2. Look around the house for other locations with pens.\n3. Bring pens from the other location to the parkour.\n4. Repeat steps 1., 2. and 3. until there are three pens in the parlor with the user."
        }
        
        ar1 = {
            "role": "assistant",
            "content": "Since I am currently at the location of the user we first need to determine how many pens I should bring. For this I call the find_object function."
        }
        
        fc1 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_1",
                "function": {
                "name": "find_object",
                "arguments": "{\n  \"object_name_list\": [\"pen\"]\n}"
                },
                "type": "function",
            }]
        }
        
        fr1 = {
            "role": "tool", 
            "tool_call_id": "call_1",
            "content": "The following items were found at/in the parlor:\npen was found 1 times.",
            "name": "find_object"
        }
        
        ar2 = {
            "role": "assistant",
            "content": "There is only 1 pen in the parlor with the user. I need to find and bring 2 other pens to the parlor. Pens are likely located in the study, so I will drive there using drive_to_location."
        }
        
        fc2 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_2",
                "function": {
                "name": "drive_to_location",
                "arguments": "{\n  \"location\": \"study\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr2 = {
            "role": "tool", 
            "tool_call_id": "call_2",
            "content": "You successfully arrived in the new location study. This is now the current location.",
            "name": "drive_to_location"
        }
        
        ar3 = {
            "role": "assistant",
            "content": "I am now in the study but need to verify that the pens I should fetch are located here. Therefore, I will need find_object."
        }
        
        fc3 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_3",
                "function": {
                "name": "find_object",
                "arguments": "{\n  \"object_name_list\": [\"pen\"]\n}"
                },
                "type": "function",
            }]
        }
        
        fr3 = {
            "role": "tool", 
            "tool_call_id": "call_3",
            "content": "The following items were found at/in the study:\npen was found 3 times.",
            "name": "find_object"
        }
        
        ar4 = {
            "role": "assistant",
            "content": "There are 3 >= 2 pens located in the study. I do not need to look at another location for pens. I can now pick up 2 pens and deliver them to the user. I achieve this with grasp_object."
        }
        
        fc4 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_4",
                "function": {
                "name": "grasp_object",
                "arguments": "{\n  \"object_name\": \"pen\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr4 = {
            "role": "tool", 
            "tool_call_id": "call_4",
            "content": "You successfully grasped the object pen.",
            "name": "grasp_object"
        }
        
        ar5 = {
            "role": "assistant",
            "content": "I have successfully grasped the first pen. Since I have two arms I can also grab the second pen before driving to the user. I need to call grasp_object again."
        }
        
        fc5 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_5",
                "function": {
                "name": "grasp_object",
                "arguments": "{\n  \"object_name\": \"pen\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr5 = {
            "role": "tool", 
            "tool_call_id": "call_5",
            "content": "You successfully grasped the object pen.",
            "name": "grasp_object"
        }
        
        ar6 = {
            "role": "assistant",
            "content": "Now that I have two pens in my hands I can drive back to the user who is located in the parlor and deliver the pens. To do this I call drive_to_location."
        }
        
        fc6 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_6",
                "function": {
                "name": "drive_to_location",
                "arguments": "{\n  \"location\": \"parlor\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr6 = {
            "role": "tool", 
            "tool_call_id": "call_6",
            "content": "You successfully arrived in the new location parlor. This is now the current location.",
            "name": "drive_to_location"
        }
        
        ar7 = {
            "role": "assistant",
            "content": "I am now in the parlor and can place the two pens one after the other to transfer them to the parlor. For placing an object I use place_object."
        }
        
        fc7 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_7",
                "function": {
                "name": "place_object",
                "arguments": "{\n  \"object_name\": \"pen\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr7 = {
            "role": "tool", 
            "tool_call_id": "call_7",
            "content": "You successfully placed the object pen.",
            "name": "grasp_object"
        }
        
        ar8 = {
            "role": "assistant",
            "content": "I have successfully placed the first pen. This means I am holding 1 pen in my hand and there are 1+1=2 pens in the parlor currently. I will set down the second pen using another place_object call."
        }
        
        fc8 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_8",
                "function": {
                "name": "place_object",
                "arguments": "{\n  \"object_name\": \"pen\"\n}"
                },
                "type": "function",
            }]
        }
        
        fr8 = {
            "role": "tool", 
            "tool_call_id": "call_8",
            "content": "You successfully placed the object pen.",
            "name": "grasp_object"
        }
        
        ar9 = {
            "role": "assistant",
            "content": "Since the second pen has been placed there are now 1 + 2 = 3 pens in the current parlor. The user is also at the parlor so there are 3 pens at the user's location. This means my task is accomplished and I can exit."
        }
        
        fc9 = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id" : "call_9",
                "function": {
                "name": "exit",
                "arguments": "{}"
                },
                "type": "function",
            }]
        }

        fr9 = {
            "role": "tool", 
            "tool_call_id": "call_9",
            "content": "You have completed the task successfully",
            "name": "grasp_object"
        }
        
        example_end = {
            "role": "system",
            "content": "This is the end of the example. The next user message will contain your task."
        }
        
        
        ars = [ar1, ar2, ar3, ar4, ar5, ar6, ar7, ar8, ar9]
        fcs = [fc1, fc2, fc3, fc4, fc5, fc6, fc7, fc8, fc9]
        frs = [fr1, fr2, fr3, fr4, fr5, fr6, fr7, fr8, fr9]
        
        llm.add_message(user_task)
        if cot_mode in ["once", "repeated"]:
            llm.create_message(role="system", content="Briefly summarize the next steps to accomplish the task in text form.")
            llm.add_message(cot)
            llm.create_message(role="system", content="From now on only use function calls and execute the task.")
        for i in range(9):
            if cot_mode == "ReAct" or cot_mode == "combined":
                llm.add_message(ars[i])
            llm.add_message(fcs[i])
            llm.add_message(frs[i])
        llm.add_message(example_end)
        
    # alternate model = gpt-4-0613   gpt-3.5-turbo-0613
    def __init__(self, robot, config_dict, task=None, call_main=True) -> None:
        self.config_dict = config_dict
        self.robot = robot
        self.llm_history = None
        self.number_of_function_calls = 0
        self.begining_length = 0
        
        self.llm = LLMManager(config_dict)
        self.fm = FunctionManager(self.robot, config_dict)
        
        if call_main:
            self.llm_history = self.main(task=task)
        
    
    
    def main(self, task=None):
        
        """
        repeated_chain_of_thought_mode can be "none", "once" or "repeated
        """
        cot_mode = self.config_dict["cot_mode"]
        cot_frequency = self.config_dict["cot_frequency"]
        n = self.config_dict["max_queries"]
        selective_functions = self.config_dict["selective_functions"]
        task_mode = self.config_dict["task_mode"]
        debug_mode = self.config_dict["debug_mode"]
        include_example = self.config_dict["include_example"]
        include_state = self.config_dict["include_state"]
        
        print(f"Using model {self.config_dict['model']}")
        llm = self.llm
        fm = self.fm
        
        self.assemble_system_prompt(cot_mode=cot_mode, task_mode=task_mode, example=include_example)
        
        #initial_msg = {"role": "assistant", "content": "Please give me my task."}
        #self.llm.add_message(initial_msg)
        self.begining_length = len(self.llm.message_history)
        
        if task == None:
            initial_msg = {"role": "assistant", "content": "Please give me my task."}
            task_msg = self.fm.get_user_interaction(initial_msg)
        else:
            task_msg = {"role": "user", "content": task}
        fm.task = task_msg["content"]
        llm.add_message(task_msg)
        
       
        
        if cot_mode == "once":
            llm.update_funtions(fm.get_available_functions(selective_mode=False))
            llm_response = self.prompt_chain_of_thought()
        
        for i in range(n):
            if include_state:
                state_msg = fm.get_robot_state_description()
                llm.add_tmp_message(state_msg)
            
            # do CoT
            if (cot_mode == "repeated" or cot_mode == "combined") and i % cot_frequency == 0:
                llm.update_funtions(fm.get_available_functions(selective_mode=False))
                llm_response = self.prompt_chain_of_thought()
            
            # update functions
            fn = fm.get_available_functions(selective_mode=selective_functions)
            # debug
            if debug_mode:
                print(fn)
                #print(fm.get_robot_state_description()["content"])
            llm.update_funtions(fn)
            
            
            # get model response
            if (cot_mode == "ReAct" or cot_mode == "combined"):
                llm_response = self.get_react_response()
            else:
                llm_response = llm.get_model_response("any")
            if debug_mode:
                print(llm_response)
            self.number_of_function_calls += 1
            
            
            robot_response, parallel_backup = fm.handle_llm_response(llm_response)
            if robot_response == "exit":
                break
            llm.add_message(robot_response)
            if parallel_backup != None:
                for r in parallel_backup:
                    llm.add_message(r)
            #sleep(2)
           
        
        print("\n=====================\nSummary:\n=====================")
        self.llm.print_message_history()
        self.llm_history = llm.message_history
        return llm.message_history
    
    def prompt_chain_of_thought(self):
        llm = self.llm
        verbose = self.config_dict["verbose_robot"]
        include_state = self.config_dict["include_state"]
        
        llm.create_message(role="system", content="Briefly summarize the next steps to accomplish the task in text form.")
        llm_response = llm.get_model_response(function_call="none")
        if verbose:
            self.fm.robot.speak(llm.message_history[-1].content)
        llm.create_message(role="system", content="From now on only use function calls and execute the task.")
        
        
        if include_state:
            state_msg = self.fm.get_robot_state_description()
            llm.add_tmp_message(state_msg)
        
        return llm_response
    
    def get_react_response(self):
        llm = self.llm
        verbose = self.config_dict["verbose_robot"]
        include_state = self.config_dict["include_state"]
        
        llm_response = llm.get_model_response(function_call="none")
        
        if include_state:
            state_msg = self.fm.get_robot_state_description()
            llm.add_tmp_message(state_msg)
        
        if verbose:
            self.fm.robot.speak(llm.message_history[-1].content)
        llm_response = llm.get_model_response(function_call="any")
        
        
        return llm_response
    
    def replay_history(self, robot):
        if self.llm_history == None or self.llm_history == []:
            raise ValueError("History is Empty")
        
        truncated_history = self.llm_history[self.begining_length:]
        
        fm = FunctionManager(robot, self.config_dict)
        fm.replay_llm_history(truncated_history)
        
    
    def save(self, path):
        # data = {
        #     "cfg": self.config_dict,
        #     "history": self.llm_history,
        #     "begining_length": self.begining_length
        # }
        with open(path, 'wb') as file:
            pickle.dump(self, file)
        return
    
    # only ment for replaying the history. Else shit will get real expensive real quick!
    def load(path):
        with open(path, 'rb') as file:
            gpsr = pickle.load(file)
        return gpsr
        
        
        
# if __name__ == "__main__":
#     robot = DummyRobot()
#     gpsr = GPSR(robot, use_speech_recognition=False)
#     gpsr.main()
    
    