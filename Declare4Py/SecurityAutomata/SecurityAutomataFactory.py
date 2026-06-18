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
        if template == "Chain Response":
            states = ["Q0", "Q1", "Q2"] 
            transitions = {("!"+actions[0], "Q0"): "Q0", (actions[0], "Q0"): "Q1", (actions[1], "Q2"): "Q0"}
            suppressions = {("!"+actions[0], "+"): "Q0", (actions[0], "Q0"): "-"}
            insertions = {("!"+actions[1], "Q1"): ([actions[0], actions[1]], "Q0"), (actions[1], "Q1"): ([actions[0]], "Q2")}
            return EditAutomaton("Q0", states, transitions, suppressions, insertions)
        elif template == "Chain Precedence":
            states = ["Q0", "Q1"]
            transitions = {(actions[1], "Q0"): "Q0", ("!"+actions[1], "Q0"): "Q1", (actions[1], "Q1"): "Q0"}
            insertions = {(actions[0], "Q1"): ([actions[1]], "Q0")}
            return InsertionAutomaton("Q0", states, transitions, insertions)
        
factory = SecurityAutomataFactory()
model_path = os.path.join(os.path.dirname(__file__), "data-model2.decl")
automata = factory.generateAutomataFromFile(model_path)


for label, automaton in automata.items():
    automaton.visualizeAutomaton(label)
