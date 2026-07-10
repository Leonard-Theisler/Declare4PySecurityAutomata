from typing import Dict, List, Tuple
import graphviz
from .OutputSequence import OutputSequence
from .TruncationAutomaton import TruncationAutomaton

class InsertionAutomaton(TruncationAutomaton):
    def __init__(self, initial_state: str,
                 states: List[str],
                 transitions: Dict[Tuple[str, str], str],
                 insertions: Dict[Tuple[str, str], Tuple[List[str], str]]):
        
            self._initial_state: str= initial_state
            self._states = states
            self._transitions = transitions
            self._insertions = insertions

            self.currentState: str = initial_state
            self.outputTrace: List[str] = []
            
    def canInsertAction(self, transition: Tuple[str, str]):
        if transition in self._insertions:
            return True
        return False
    
    def fireInsertTransition(self, transition: Tuple[str, str]):
        self.currentState = self._insertions[transition][1]
        
        for action in self._insertions[transition][0]:
            self.outputTrace.append(action)
        
    def runTrace(self, trace: List[str]):
        output = OutputSequence()
        self.currentState = self._initial_state
        self.outputTrace = []        
        
        if trace == [""]:
            output.outputTrace = trace
            return output
        
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

            else:
                self.fireTransition((action, self.currentState))

            i += 1
            
        output.outputTrace = self.outputTrace
        return output

    
    def visualizeAutomaton(self, filename: str):
        automaton = graphviz.Digraph(comment = "Insertion Automaton", engine = "dot")
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
            automaton.edge(transition[1], self._transitions[transition], label = transition[0])
        for insertTransition in self._insertions:
            #with inserted actions below the edge, looks funky
            # automaton.edge(insertTransition[1], self._insertions[insertTransition][1], label = insertTransition[0], xlabel = ' ,'.join(self._insertions[insertTransition][0]), color="blue")
            automaton.edge(insertTransition[1], self._insertions[insertTransition][1], label = insertTransition[0], color="blue")

        automaton.render(filename, view = True)
                
# insertionAutomaton = InsertionAutomaton("Qnfr", 
#                                         ["Qnfr", "Qfr"], 
#                                         {("not FileRead", "Qnfr"): "Qnfr", ("FileRead", "Qnfr"): "Qfr", ("not Send", "Qfr"): "Qfr"},
#                                         {("not FileRead", "Qfr"): (["FileRead"], "Qnfr")})
# output = insertionAutomaton.runTrace(["not FileRead", "FileRead", "not Send", "not FileRead"])
# insertionAutomaton.visualizeAutomaton("No Send after FileRead with insertion")

# print(output.traceAcceptance)
# print(output.outputTrace)
# print(output.insertions)
