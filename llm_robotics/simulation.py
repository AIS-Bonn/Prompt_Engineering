from llm_robotics.gpsr import GPSR
import openai
import random

def split_integer_into_boxes(n, num_boxes):
    """
    Splits a positive integer n randomly across a specified number of boxes.

    Parameters:
    - n: The positive integer to be split.
    - num_boxes: The number of boxes among which to split the integer.

    Returns:
    A list of positive integers that sum up to n, representing the split across the boxes.
    """
    if n <= 0 or num_boxes <= 0:
        raise ValueError("Both n and num_boxes must be positive integers")

    # Generate num_boxes-1 random split points
    split_points = sorted(random.sample(range(1, n), num_boxes - 1))

    # Initialize the list of splits with the first split point
    splits = [split_points[0]]

    # Calculate the differences between consecutive split points for the remaining splits
    for i in range(1, len(split_points)):
        splits.append(split_points[i] - split_points[i-1])

    # Add the last split, which is the difference between n and the last split point
    splits.append(n - split_points[-1])

    return splits

class Simulation:
    
    def __init__(self, seed=0, mode="no_input") -> None:
        self.mode = mode
        #self.task = "Bring me an apple from the study."
        #self.task = "There are apples, bananas and strawberries strewn about the house. Please distribute them so that each location has an equal number of fruit."
        self.task  = "Bring me a bottle."
        #self.task = "Distribute the apples which are strewn about the house so that each location has at least one."
        #self.task = "There are apples, bananas and strawberries. Distribute the fruit which are strewn about the house so that each location has at least one."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["apple", "strawberry", "banana", "bottle"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "apple": 0,
                "strawberry": 2,
                "banana": 0,
                "bottle": 0,
            },
            "kitchen": {
                "apple": 3,
                "strawberry": 0,
                "banana": 1,
                "bottle": 1,
            },
            "study": {
                "apple": 0,
                "strawberry": 0,
                "banana": 0,
                "bottle": 2,
            },
            "parlor": {
                "apple": 2,
                "strawberry": 1,
                "banana": 0,
                "bottle": 0,
            },
        }
        pass
    
    def recognize_speech(self):
        if self.mode == "input":
            return input("User input: ")
        else:
            return "I have no other tasks for you."
    
    def speak(self, text):
        return True
    
    def let_customer_get_object(self, arm = "left"):
        # whether the item is in one hand is checked in robot_interface
        
        self.items_by_location[self.location][self.arms[arm]] += 1
        self.arms[arm] = None
            
        return True
        
    def handover_object(self, object_name, arm="left", attach_as_collision_object=False):
        if object_name not in self.items:
            return False
        
        arm = None
        if self.arms["left"] == None:
            arm = "left"
        elif self.arms["right"] == None:
            arm = "right"
        else:
            return False
        
        if self.items_by_location[self.location][object_name] == 0:
            return False
        
        self.items_by_location[self.location][object_name] -= 1
        self.arms[arm] = object_name
        
        return True
    
    def drive_to_location(self, location):
        if location in self.locations:
            self.location = location
            return True
        else:
            return False
    
    def find_object_detic(self, object_name_list):
        detections = []
        for object in object_name_list:
            if object in self.items:
                for i in range(self.items_by_location[self.location][object]):
                    detections.append(object)
            
        return detections
    
    def check_success(self):
        raise NotImplementedError
    
    
    
class DistributeApples(Simulation):
        
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Distribute the apples which are strewn about the house so that each location has at least one."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["apple"]
        self.items_by_location = {
            "bedroom": {
                "apple": 0,
            },
            "kitchen": {
                "apple": 4,
            },
            "study": {
                "apple": 0,
            },
            "parlor": {
                "apple": 1,
            },
        }
    
    def check_success(self):
        success = True
        
        for location in self.locations:
            if self.items_by_location[location]["apple"] < 1:
                success = False
            
        return success
    
    
class DistributeFruit(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "There are apples, bananas and strawberries. Distribute the fruit which are strewn about the house so that each location has at least one piece of fruit."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["apple", "strawberry", "banana"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "apple": 0,
                "strawberry": 0,
                "banana": 0,
            },
            "kitchen": {
                "apple": 3,
                "strawberry": 0,
                "banana": 1,
            },
            "study": {
                "apple": 0,
                "strawberry": 0,
                "banana": 1,
            },
            "parlor": {
                "apple": 0,
                "strawberry": 3,
                "banana": 0,
            },
        }
        
    def check_success(self):
        success = True
        
        for location in self.locations:
            fruit = 0
            for item in self.items:
                fruit += self.items_by_location[location][item]
            if fruit < 1:
                success = False
    
            
        return success
    
    
class FetchAndCount(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Please ensure that the number of apples in the parlor is equal to the number of bottles in the parlor."
        self.items = ["apple", "bottle"]
        self.items_by_location = {
            "bedroom": {
                "apple": 2,
                "bottle": 0,
            },
            "kitchen": {
                "apple": 3,
                "bottle": 0,
            },
            "study": {
                "apple": 0,
                "bottle": 2,
            },
            "parlor": {
                "apple": 0,
                "bottle": 2,
            },
        }
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if parlor_items["apple"] != parlor_items["bottle"]:
            success = False
            
        return success
    
    
class SimpleFetch(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Please bring me an apple from the kitchen."
        self.items = ["apple", "bottle"]
        self.items_by_location = {
            "bedroom": {
                "apple": 0,
                "bottle": 0,
            },
            "kitchen": {
                "apple": 1,
                "bottle": 0,
            },
            "study": {
                "apple": 3,
                "bottle": 0,
            },
            "parlor": {
                "apple": 0,
                "bottle": 0,
            },
        }
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if parlor_items["apple"] < 1:
            success = False
            
        kitchen_items = self.items_by_location["kitchen"]
        if kitchen_items["apple"] > 0:
            success = False
            
        return success
    
    

    


class TestSimpleFetch(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Please bring me a banana."
        self.items = ["banana", "bottle"]
        self.items_by_location = {
            "bedroom": {
                "banana": 0,
            },
            "kitchen": {
                "banana": 2,
            },
            "study": {
                "banana": 0,
            },
            "parlor": {
                "banana": 0,
            },
        }
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if parlor_items["banana"] < 1:
            success = False
            
        kitchen_items = self.items_by_location["kitchen"]
        if kitchen_items["banana"] > 1:
            success = False
            
        return success
    
class TestFetchAndCount(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Please ensure that the number of forks in the parlor is equal to the number of knifes in the parlor."
        self.items = ["knife", "fork"]
        self.items_by_location = {
            "bedroom": {
                "fork": 0,
                "knife": 1,
            },
            "kitchen": {
                "fork": 4,
                "knife": 2,
            },
            "study": {
                "fork": 1,
                "knife": 3,
            },
            "parlor": {
                "fork": 0,
                "knife": 3,
            },
        }
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if parlor_items["fork"] != parlor_items["knife"]:
            success = False
            
        return success
    
    
class TestDistributeTableware(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "There are knifes, forks and spoons strewn about different locations in the apartment. Distribute the tableware so that each location has at least one piece of tableware."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["knife", "fork", "spoon"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "knife": 0,
                "fork": 0,
                "spoon": 0,
            },
            "kitchen": {
                "knife": 0,
                "fork": 0,
                "spoon": 1,
            },
            "study": {
                "knife": 0,
                "fork": 0,
                "spoon": 0,
            },
            "parlor": {
                "knife": 3,
                "fork": 2,
                "spoon": 0,
            },
        }
        
    def check_success(self):
        success = True
        
        for location in self.locations:
            tableware = 0
            for item in self.items:
                tableware += self.items_by_location[location][item]
            if tableware < 1:
                success = False
    
            
        return success
    
    
class TestDistributeBottles(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "The apartment contains bottles. Ensure that each location except the kitchen has exactly one bottle."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["bottle"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "bottle": 0,
            },
            "kitchen": {
                "bottle": 3,
            },
            "study": {
                "bottle": 0,
            },
            "parlor": {
                "bottle": 2,
            },
        }
        
    def check_success(self):
        success = True
        
        for location in ["bedroom", "study", "parlor"]:
            if self.items_by_location[location]["bottle"] != 1:
                success = False
    
            
        return success
    
class TestSoup(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "I want to eat soup for dinner. Bring me all related items."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["soup", "bowl", "spoon"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "soup": 0,
                "bowl": 0,
                "spoon": 0,
            },
            "kitchen": {
                "soup": 1,
                "bowl": 1,
                "spoon": 2,
            },
            "study": {
                "soup": 0,
                "bowl": 0,
                "spoon": 0,
            },
            "parlor": {
                "soup": 0,
                "bowl": 0,
                "spoon": 0,
            },
        }
        
    def check_success(self):
        success = True
        
        if self.items_by_location["parlor"]["soup"] < 1:
            success = False
        if self.items_by_location["parlor"]["bowl"] < 1:
            success = False
        if self.items_by_location["parlor"]["spoon"] < 1:
            success = False
    
        return success
    
class TestFetchAndCount2(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "Fetch enough apples from the kitchen so that the parlor has an equal number of apples and bananas."
        self.items = ["banana", "apple"]
        self.items_by_location = {
            "bedroom": {
                "banana": 0,
                "apple": 1,
            },
            "kitchen": {
                "banana": 1,
                "apple": 3,
            },
            "study": {
                "banana": 0,
                "apple": 1,
            },
            "parlor": {
                "banana": 2,
                "apple": 0,
            },
        }
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if parlor_items["banana"] != parlor_items["apple"]:
            success = False
            
        return success
    
class TestDistribute2(Simulation):
    
    def __init__(self, seed=0) -> None:
        super().__init__()
        self.task = "The apartment contains oranges. Ensure that each location except the kitchen has exactly one orange. Extra oranges can be gotten or deposited in the kitchen."
        self.location = "parlor"
        self.locations = ["bedroom", "kitchen", "study", "parlor"]
        self.items = ["orange"]
        self.arms = {
            "left": None,
            "right": None,
        }
        self.items_by_location = {
            "bedroom": {
                "orange": 0,
            },
            "kitchen": {
                "orange": 3,
            },
            "study": {
                "orange": 0,
            },
            "parlor": {
                "orange": 2,
            },
        }
        
    def check_success(self):
        success = True
        
        for location in ["bedroom", "study", "parlor"]:
            if self.items_by_location[location]["orange"] != 1:
                success = False
    
            
        return success
    

class RandomFetch(Simulation):
    
    def __init__(self, seed: int) -> None:
        super().__init__()
        random.seed(seed)
        self.standard_location_items = {"kitchen": ["banana", "apple", "knife", "fork", "spoon", "orange", "sponge"],
                                           "bedroom": ["comb"],
                                           "study": ["pen", "pencil", "key"],
                                           "parlor": [],
                                           }
        self.items_to_location = {x: key for key, items in self.standard_location_items.items() for x in items}
        self.items = [item for items in self.standard_location_items.values() for item in items]



        self.items_by_location = {
            "bedroom": {item: random.randint(0, 3) for item in self.items},
            "kitchen": {item: random.randint(0, 3) for item in self.items},
            "study": {item: random.randint(0, 3) for item in self.items},
            "parlor": {item: random.randint(0, 3) for item in self.items},
        }

        self.selected_item = random.choice(self.items)

        self.selected_item_location = self.items_to_location[self.selected_item]
        self.items_by_location["parlor"][self.selected_item] = 0
        self.items_by_location[self.selected_item_location][self.selected_item] = random.randint(1, 3)
        
        self.task = f"Please bring me a{'n' if self.selected_item[0] in 'aeiou' else ''} {self.selected_item} from the {self.selected_item_location}."
    
    def check_success(self):
        success = True
        
        parlor_items = self.items_by_location["parlor"]
        if self.items_by_location["parlor"][self.selected_item] == 0:
            success = False
            
        return success
    


class RandomConditional(Simulation):
    
    def __init__(self, seed: int) -> None:
        super().__init__()
        random.seed(seed + 2**8)
        self.standard_location_items = {"kitchen": ["banana", "apple", "knife", "fork", "spoon", "orange", "sponge"],
                                           "bedroom": ["comb"],
                                           "study": ["pen", "pencil", "key"],
                                           "parlor": [],
                                           }
        self.items_to_location = {x: key for key, items in self.standard_location_items.items() for x in items}
        self.items = [item for items in self.standard_location_items.values() for item in items]



        self.items_by_location = {
            "bedroom": {item: random.randint(0, 3) for item in self.items},
            "kitchen": {item: random.randint(0, 3) for item in self.items},
            "study": {item: random.randint(0, 3) for item in self.items},
            "parlor": {item: random.randint(0, 3) for item in self.items},
        }

        self.selected_items = random.sample(self.items, 3)
        random.shuffle(self.selected_items)
        self.selected_item_locations = [self.items_to_location[item] for item in self.selected_items]

        for item in self.selected_items:
            self.items_by_location["parlor"][item] = 0
        self.selector = random.randint(0, 1)
        self.items_by_location[self.selected_item_locations[0]][self.selected_items[0]] = self.selector
        self.items_by_location[self.selected_item_locations[1]][self.selected_items[1]] = random.randint(1, 3)
        self.items_by_location[self.selected_item_locations[2]][self.selected_items[2]] = random.randint(1, 3)
        
        self.task = (f"Check if there is a{'n' if self.selected_items[0][0] in 'aeiou' else ''} {self.selected_items[0]} in the {self.selected_item_locations[0]}. " + 
                     f"Should you find one, bring me a{'n' if self.selected_items[1][0] in 'aeiou' else ''} {self.selected_items[1]} from the {self.selected_item_locations[1]}. " +
                     f"Otherwise, bring me a{'n' if self.selected_items[2][0] in 'aeiou' else ''} {self.selected_items[2]} from the {self.selected_item_locations[2]}.")
    
    def check_success(self):
        success = False
        not_selector =  1 - self.selector
        if self.items_by_location["parlor"][self.selected_items[1 + not_selector]] > 0:
            if self.items_by_location["parlor"][self.selected_items[1 + self.selector]] == 0:
                success = True
            
        return success
    
class RandomDistribute(Simulation):
    
    def __init__(self, seed: int) -> None:
        super().__init__()
        random.seed(seed + 2**9)
        self.standard_location_items = {"kitchen": ["banana", "apple", "knife", "fork", "spoon", "orange", "sponge"],
                                           "bedroom": ["comb"],
                                           "study": ["pen", "pencil", "key"],
                                           "parlor": [],
                                           }
        self.items_to_location = {x: key for key, items in self.standard_location_items.items() for x in items}
        self.items = [item for items in self.standard_location_items.values() for item in items]



        self.items_by_location = {
            "bedroom": {item: random.randint(0, 3) for item in self.items},
            "kitchen": {item: random.randint(0, 3) for item in self.items},
            "study": {item: random.randint(0, 3) for item in self.items},
            "parlor": {item: random.randint(0, 3) for item in self.items},
        }

        self.selected_item = random.choice(self.items)
        self.selected_item_location = self.items_to_location[self.selected_item]


        split = random.randint(0, 1)
        for location in self.locations:
            self.items_by_location[location][self.selected_item] = 0
        self.items_by_location["parlor"][self.selected_item] = 1 + split
        self.items_by_location[self.selected_item_location][self.selected_item] = 3 + (1 - split)
        
        self.task = (f"Please evenly distribute {self.selected_item}s so that each location contains at least one {self.selected_item}. " +
                     f"You can start with the {self.selected_item}s in the {self.selected_item_location}.")
    
    def check_success(self):
        success = True
        for location in self.locations:
            if self.items_by_location[location][self.selected_item] < 1:
                success = False
            
        return success
    

class RandomEquals(Simulation):
    
    def __init__(self, seed: int) -> None:
        super().__init__()
        random.seed(seed + 2**10)
        self.standard_location_items = {"kitchen": ["banana", "apple", "knife", "fork", "spoon", "orange", "sponge"],
                                           "bedroom": ["comb"],
                                           "study": ["pen", "pencil", "key"],
                                           "parlor": [],
                                           }
        self.items_to_location = {x: key for key, items in self.standard_location_items.items() for x in items}
        self.items = [item for items in self.standard_location_items.values() for item in items]



        self.items_by_location = {
            "bedroom": {item: random.randint(0, 3) for item in self.items},
            "kitchen": {item: random.randint(0, 3) for item in self.items},
            "study": {item: random.randint(0, 3) for item in self.items},
            "parlor": {item: random.randint(0, 3) for item in self.items},
        }

        self.selected_item_1 = random.choice(self.items) # item to deliver
        self.selected_item_2 = random.choice(self.items) # item to reference
        if self.selected_item_1 == self.selected_item_2:
            self.selected_item_2 = random.choice(self.items)


        self.selected_item_location_1 = self.items_to_location[self.selected_item_1]
        self.selected_item_location_2 = self.items_to_location[self.selected_item_2]
        self.target_number = random.randint(2, 3)
        self.pralor_item = random.randint(0, 1)


        self.items_by_location[self.selected_item_location_1][self.selected_item_1] = self.target_number + random.randint(0, 2)
        self.items_by_location[self.selected_item_location_2][self.selected_item_2] = self.target_number
        self.items_by_location["parlor"][self.selected_item_1] = 0
        
        #self.task = (f"Bring one {self.selected_item_1} to the parlor for every {self.selected_item_2} in the {self.selected_item_location_2}. {self.selected_item_1}s can be found in the {self.selected_item_location_1}.")
        self.task = (f"For each {self.selected_item_2} in the {self.selected_item_location_2}, move a {self.selected_item_1} from the {self.selected_item_location_1} to the parlor.")
    
    def check_success(self):
        success = False
        if self.items_by_location["parlor"][self.selected_item_1] == self.target_number:
            success = True
            
        return success
    
    

if __name__ == "__main__":
    

    r1 = RandomFetch(1)
    r2 = RandomConditional(2)
    r3 = RandomEquals(1)
    r4 = RandomDistribute(1)

    for r in [r1, r2, r3, r4]:
        print(r.task)
        #print(r.items_by_location)
        print("###############")

