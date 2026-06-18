from typing import Dict, List, Tuple
import graphviz
from SuppressionAutomaton import SuppressionAutomaton
from InsertionAutomaton import InsertionAutomaton
from OutputSequence import OutputSequence

class EditAutomaton(SuppressionAutomaton, InsertionAutomaton):
    
    def __init__(self, initial_state: str,
                 states: List[str],
                 transitions: dict[Tuple[str, str], str],
                 suppressions: dict[Tuple[str, str], str],
                 insertions: dict[Tuple[str, str], Tuple[List[str], str]]):
        
        self._initial_state: str= initial_state
        self._states = states
        self._transitions = transitions
        self._insertions = insertions
        self._suppressions = suppressions

        self.currentState: str = initial_state
        self.outputTrace: List[str] = []
        
    def runTrace(self, trace: List[str]):
        output = OutputSequence()
        i = 0
        while i < len(trace):
            action = trace[i]
            if not self.canExecuteAction((action, self.currentState)) and not self.canInsertAction((action, self.currentState)):
                output.outputTrace = self.outputTrace
                output.addTuncation(action, self.currentState, i)
                break
            elif self.canInsertAction((action, self.currentState)):  
                output.addInsertion(self._insertions[(action, self.currentState)][0], self.currentState, i)                                                
                self.fireInsertTransition((action, self.currentState))
                continue    
            elif self.suppressAction((action, self.currentState)):
                output.addSuppression(action, self.currentState, i)
                self.fireSuppressedTransition((action, self.currentState))
            else:
                self.fireTransition((action, self.currentState))

            i += 1
            
        output.outputTrace = self.outputTrace
        return output
            
    def visualizeAutomaton(self, filename: str):
        automaton = graphviz.Digraph(comment = "Edit Automaton", engine = "dot")
        automaton.attr(rankdir='LR')
        automaton.node("start", label = "", shape = "none")

        for state in self._states:
            if state.startswith("Q"):
                label = f'<Q<SUB>{state[1:]}</SUB>>'
            else:
                label = state
            automaton.node(state, label =label, shape = "circle", fixedsize="true", width="0.8")
        
        automaton.edge("start", self._initial_state, headport = "sw")

        for transition in self._transitions:
            if transition in self._suppressions and self._suppressions[transition] == "-":
                automaton.edge(transition[1], self._transitions[transition], label = transition[0], color="red")
            else:
                automaton.edge(transition[1], self._transitions[transition], label = transition[0])
        for insertTransition in self._insertions:
            #with inserted actions below the edge, looks funky
            # automaton.edge(insertTransition[1], self._insertions[insertTransition][1], label = insertTransition[0], xlabel = ' ,'.join(self._insertions[insertTransition][0]), color="blue")
            automaton.edge(insertTransition[1], self._insertions[insertTransition][1], label = insertTransition[0],  color="blue")

        automaton.render(filename, view = True)
        
editAutomaton = EditAutomaton("Q0",
                              ["Q0", "Q1", "Q2", "Q3"],
                              {("show", "Q0"): "Q0", ("board", "Q0"): "Q1", ("show", "Q2"): "Q3", ("show", "Q3"): "Q3"},
                              {("show", "Q0"): "+", ("board", "Q0"): "-", ("show", "Q2"): "+", ("show", "Q3"): "+"},
                              {("board", "Q1"): (["board","show"], "Q3"), ("show", "Q1"): (["board"], "Q2")})                  
output = editAutomaton.runTrace(["board", "show"]) #board, show
# output = editAutomaton.runTrace(["board", "board"]) #board, show
# output = editAutomaton.runTrace(["show", "board", "show"]) #show, board, show

# editAutomaton.visualizeAutomaton("Edit Automaton")

# print(output.traceAcceptance)
# print(output.outputTrace)
# print("suppressions: " , output.suppressions)
# print("insertions: " , output.insertions)
# print("truncations: ", output.truncation)
