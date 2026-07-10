from typing import Dict, List, Tuple
import graphviz
from .OutputSequence import OutputSequence

class TruncationAutomaton:
    
    def __init__(self, initial_state: str,
                 states: List[str],
                 transitions: Dict[Tuple[str, str], str]):
        
        self._initial_state: str= initial_state
        self._states = states
        self._transitions = transitions

        self.currentState: str = initial_state
        self.outputTrace: List[str] = []


    def canExecuteAction(self, transition: Tuple[str, str]):
        if transition in self._transitions:
            return True
        return False
    
    def fireTransition(self, transition):
        self.currentState = self._transitions[transition]
        self.outputTrace.append(transition[0])

    def printAutomaton(self):
        print("The initial state is: ", self._initial_state)
        print("The automaton has states: ")
        print("The transitions are: ", ",".join(self.states))
        for transition in self._transitions:
            print(transition, " -> ", self._transitions[transition])
        print("The automaton is currently in state: ", self.currentState)


    def runTrace(self, trace: List[str]):
        output = OutputSequence()
        self.currentState = self._initial_state
        self.outputTrace = []
        
        if trace == [""]:
            output.outputTrace = trace
            return output
        
        index = 0
        for action in trace:
            if not self.canExecuteAction((action, self.currentState)):
                output.outputTrace = self.outputTrace
                output.addTuncation(action, self.currentState, index)
                break
            self.fireTransition((action, self.currentState))
            index += 1

        output.outputTrace = self.outputTrace
        return output

    def visualizeAutomaton(self, filename: str):
        automaton = graphviz.Digraph(comment = "Truncation Automaton")
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

        automaton.render(filename, view = True)

    

# securityAutomaton = TruncationAutomaton("Qnfr", ["Qnfr", "Qfr"], {("not FileRead", "Qnfr"): "Qnfr", ("FileRead", "Qnfr"): "Qfr", ("not Send", "Qfr"): "Qfr"})
# output = securityAutomaton.runTrace(["not FileRead", "FileRead", "not Send", "Send"])
#securityAutomaton.visualizeAutomaton("No Send after FileRead")

# print(output.traceAcceptance)
# print(output.outputTrace)
# print(output.truncation)


