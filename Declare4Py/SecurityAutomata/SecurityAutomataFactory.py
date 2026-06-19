from Declare4Py.ProcessModels.DeclareModel import DeclareModel, DeclareModelTemplate
import os
from typing import List
from InsertionAutomaton import InsertionAutomaton
from SuppressionAutomaton import SuppressionAutomaton 
from TruncationAutomaton import TruncationAutomaton
from EditAutomaton import EditAutomaton

class SecurityAutomataFactory:
    
    def generateAutomataFromFile(self, filepath):
        constraints: dict[str, List[str]] = self.createProcessDictFromPath(filepath)
        
        automata: dict[str, object] = {}
        for template, actions in constraints.items():
            constraint = template + "(" + ",".join(action for action in actions)+")"
            automata[constraint] = self.generateAutomatonFromTemplate(template, actions)
            
        return automata
        
        
    def createProcessDictFromPath(self, filepath):
        declare_model = DeclareModel().parse_from_file(filepath)    
        templates = declare_model.parsed_model.templates
        
        declare_constraints = {}
        for template in templates:
            declare_template = templates[template]._template_name
            declare_constraints[declare_template] = []
            
            for event in templates[template].events_activities:
                if event != None:
                    declare_constraints[declare_template].append(event.event_name.value)
                else:
                    declare_constraints[declare_template].append(None)
        return declare_constraints
              
    def generateAutomatonFromTemplate(self, template: str, actions: List[str]):
        match template:
            case "At Least One": #TODO implement buffer case in insert/edit automaton
                states = ["Q0", "Q1", "Q2"]
                transitions = {("!"+actions[0], "Q0"): "Q0", (actions[0], "Q1"): "Q2"}
                suppressions = {("!"+actions[0], "Q0"): "-", (actions[0], "Q1"): "+"}
                insertions = {(actions[0], "Q0"): (["buffer"], "Q1")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "At Most One":
                states = ["Q0", "Q1"]
                transitions = {("!"+actions[0], "Q0"): "Q0", (actions[0], "Q0"): "Q1", ("!"+actions[0], "Q1"): "Q1"}
                return TruncationAutomaton("Q0", states, transitions)
            case "Init":
                states = ["Q0", "Q1"]
                transitions = {(actions[0], "Q0"): "Q1"}
                insertions = {("!"+actions[0], "Q0"): ([actions[0]], "Q1")}
                return InsertionAutomaton("Q0", states, transitions, insertions)
            case "End": #buffer case
                states = ["Q0", "Q1", "Q2"]
                transitions = {(actions[0], "Q0"): "Q0", ("!"+actions[0], "Q0"): "Q1", (actions[0], "Q2"): "Q0", ("!"+actions[0], "Q1"): "Q1"}
                suppressions = {(actions[0], "Q0"): "+", ("!"+actions[0], "Q0"): "-", (actions[0], "Q2"): "+", ("!"+actions[0], "Q1"): "-"}
                insertions = {(actions[0], "Q1"): (["buffer"], "Q2")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Responded Existence": #buffer
                states = ["Q0", "Q1", "Q2", "Q3"]
                transitions = {("!"+ actions[0]+" and !"+actions[1], "Q0"): "Q0",(actions[0], "Q0"): "Q1", ("!"+actions[1], "Q1"): "Q1", (actions[1], "Q2"): "Q3", ("true", "Q3"): "Q3", (actions[1], "Q0"): "Q3"}
                suppressions = {("!"+ actions[0]+" and !"+actions[1], "Q0"): "+",(actions[0], "Q0"): "-", ("!"+actions[1], "Q1"): "-", (actions[1], "Q2"): "+", ("true", "Q3"): "+", (actions[1], "Q0"): "+"}
                insertions ={(actions[1], "Q1"): (["buffer"], "Q2")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Response": #buffer
                states = ["Q0", "Q1", "Q2"]
                transitions = {("!" + actions[0], "Q0"): "Q0", (actions[1], "Q0"): "Q0", (actions[0], "Q0"): "Q1", ("!"+actions[1], "Q1"): "Q1", (actions[1], "Q2"): "Q0"}
                suppressions = {("!" + actions[0], "Q0"): "+",(actions[1], "Q0"): "+", (actions[0], "Q0"): "-", ("!"+actions[1], "Q1"): "-", (actions[1], "Q2"): "+"}
                insertions = {(actions[1], "Q1"): (["buffer"], "Q2")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Alternate Response": #buffer
                states = ["Q0", "Q1", "Q2"]
                transitions = {("!"+ actions[0]+" and !"+actions[1], "Q1"): "Q1", (actions[0]+" and "+actions[1], "Q1"): "Q1",("!"+actions[0], "Q0"): "Q0", (actions[0], "Q0"): "Q1", (actions[1], "Q2"): "Q0"}
                suppressions = {("!"+ actions[0]+" and !"+actions[1], "Q1"): "-", (actions[0]+" and "+actions[1], "Q1"): "-", ("!"+actions[0], "Q0"): "+", (actions[0], "Q0"): "-", (actions[1], "Q2"): "+"}
                insertions = {(actions[1], "Q1"): (["buffer"], "Q2"), (actions[0], "Q1"): (["buffer", actions[1]], "Q0")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Chain Response": #buffer
                states = ["Q0", "Q1", "Q2"] 
                transitions = {(actions[0]+" and "+actions[1], "Q1"): "Q1",("!"+actions[0], "Q0"): "Q0", (actions[0], "Q0"): "Q1", (actions[1], "Q2"): "Q0"}
                suppressions = {(actions[0]+" and "+actions[1], "Q1"): "-", ("!"+actions[0], "Q0"): "+", (actions[0], "Q0"): "-", (actions[1], "Q2"): "+"}
                insertions = {("!"+actions[1], "Q1"): (["buffer", actions[1]], "Q0"), (actions[1], "Q1"): (["buffer"], "Q2")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Precedence":
                states = ["Q0", "Q1"]
                transitions = {("!"+actions[0]+" and !"+actions[1], "Q0"): "Q0",(actions[1], "Q0"): "Q1", ("True", "Q1"): "Q1"}
                suppressions = {("!"+actions[0]+" and !"+actions[1], "Q0"): "+",(actions[1], "Q0"): "+", ("True", "Q1"): "+"}
                insertions = {(actions[0], "Q0"): ([actions[1]], "Q1")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Alternate Precedence": #buffer
                states = ["Q0", "Q1", "Q2", "Q3", "Q4"] 
                transitions = {(actions[0]+" and "+actions[1], "Q2"): "Q2", ("!"+actions[0]+" and !"+actions[1], "Q4"): "Q0",(actions[0]+" and "+actions[1], "Q0"): "Q2",("!"+actions[0]+" and !"+actions[1], "Q0"): "Q0",(actions[1], "Q0"): "Q1", ("!"+actions[0], "Q1"): "Q1", (actions[0], "Q1"): "Q2", (actions[1], "Q3"): "Q1"}
                suppressions = {(actions[0]+" and "+actions[1], "Q2"): "-", ("!"+actions[0]+" and !"+actions[1], "Q4"): "+",(actions[0]+" and "+actions[1], "Q0"): "-",("!"+actions[0]+" and !"+actions[1], "Q0"): "+",(actions[1], "Q0"): "+", ("!"+actions[0], "Q1"): "+", (actions[0], "Q1"): "-", (actions[1], "Q3"): "+"}
                insertions = {(actions[1], "Q2"): (["buffer"], "Q3"),("!"+actions[0]+" and !"+actions[1], "Q2"): (["buffer"], "Q4")}
                return EditAutomaton("Q0", states, transitions, suppressions, insertions)
            case "Chain Precedence":
                states = ["Q0", "Q1"]
                transitions = {("!"+actions[0]+" and !"+actions[1], "Q1"): "Q1", (actions[1], "Q0"): "Q0", ("!"+actions[1], "Q0"): "Q1", (actions[1], "Q1"): "Q0"}
                insertions = {(actions[0], "Q1"): ([actions[1]], "Q0")}
                return InsertionAutomaton("Q0", states, transitions, insertions)
            case "Not Responded Existence":
                states = ["Q0", "Q1", "Q2"]
                transitions = {("!"+actions[0]+" and !"+actions[1], "Q0"): "Q0",(actions[0], "Q0"): "Q2", (actions[1], "Q0"): "Q1", ("!"+actions[1], "Q2"): "Q2", ("!"+actions[0], "Q1"): "Q1", ("!"+actions[0]+" and !"+actions[1], "Q0"): "Q0"}
                return TruncationAutomaton("Q0", states, transitions)
            case "Not Response":
                states = ["Q0", "Q1"]
                transitions = {(actions[0], "Q0"): "Q1", ("!"+actions[0], "Q0"): "Q0", ("!"+actions[1], "Q1"): "Q1"}
                return TruncationAutomaton("Q0", states, transitions)
            case "Not Chain Response":
                states = ["Q0", "Q1"]
                transitions = {(actions[0], "Q0"): "Q1", ("!"+actions[0], "Q0"): "Q0", (actions[0], "Q1"): "Q1", ("!"+actions[0]+" and !"+actions[1], "Q1"): "Q0"}
                insertions = {(actions[1], "Q1"): (["!"+actions[0]+" and !"+actions[1]], "Q0")}
                return InsertionAutomaton("Q0", states, transitions, insertions)
            case "Not Precedence":
                states = ["Q0", "Q1"]
                transitions = {("!"+actions[0], "Q0"): "Q0", (actions[0], "Q0"): "Q1", ("!"+actions[1], "Q1"): "Q1"}
                return TruncationAutomaton("Q0", states, transitions)
            case "Not Chain Precedence":
                states = ["Q0", "Q1"]
                transitions = {(actions[0], "Q0"): "Q1", ("!"+actions[0], "Q0"): "Q0", (actions[0], "Q1"): "Q1", ("!"+actions[0]+" and !"+actions[1], "Q1"): "Q0"}
                insertions = {(actions[1], "Q1"): (["!"+actions[0]+" and !"+actions[1]], "Q0")}
                return InsertionAutomaton("Q0", states, transitions, insertions)
            
        
factory = SecurityAutomataFactory()
# model_path = os.path.join(os.path.dirname(__file__), "data-model2.decl")
# automata = factory.generateAutomataFromFile(model_path)


# for label, automaton in automata.items():
#     automaton.visualizeAutomaton(label)

aut = factory.generateAutomatonFromTemplate("Alternate Precedence", ["x", "y"])
# output = aut.runTrace(["y", "!x", "x", "x and y", "y"])
# print(output.traceAcceptance)
# print(output.outputTrace)
# print("suppressions: ", output.suppressions)
# print("insertions: ", output.insertions)
# print("buffer: ", output.buffer)
aut.visualizeAutomaton("Alternate Precedence x y")
