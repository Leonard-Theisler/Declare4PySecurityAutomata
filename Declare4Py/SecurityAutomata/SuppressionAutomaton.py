from fileinput import filename
from typing import Dict, List, Tuple
import graphviz
from OutputSequence import OutputSequence
from TruncationAutomaton import TruncationAutomaton

class SuppressionAutomaton(TruncationAutomaton):

        def __init__(self, initial_state: str,
                 states: List[str],
                 transitions: dict[Tuple[str,str], str],
                 suppressions: dict[Tuple[str, str,], str]):
        
            self._initial_state: str= initial_state
            self._states = states
            self._transitions = transitions
            self._suppressions = suppressions

            self.currentState: str = initial_state
            self.outputTrace: List[str] = []

        def suppressAction(self, transition: Tuple[str, str]):
            if self._suppressions[transition] == "+":
                return False
            return True
        
        def fireSuppressedTransition(self, transition: str):
            self.currentState = self._transitions[transition]

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
                elif self.suppressAction((action, self.currentState)):
                    output.addSuppression(action, self.currentState, index)
                    self.fireSuppressedTransition((action, self.currentState))
                else:
                    self.fireTransition((action, self.currentState))
                index += 1
                
            output.outputTrace = self.outputTrace
            return output        
                
        def visualizeAutomaton(self, filename: str):
            automaton = graphviz.Digraph(comment = "Suppression Automaton", engine = "dot")
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

            automaton.render(filename, view = True)
                
# suppressionAutomaton = SuppressionAutomaton("Qnfr", ["Qnfr", "Qfr"], {("not FileRead", "Qnfr"): "Qnfr", ("FileRead", "Qnfr"): "Qfr", ("not Send", "Qfr"): "Qfr", ("Send", "Qfr"): "Qfr"}, {("not FileRead", "Qnfr"): "+", ("FileRead", "Qnfr"): "+", ("not Send", "Qfr"): "+", ("Send", "Qfr"): "-"})
# output = suppressionAutomaton.runTrace(["not FileRead", "FileRead", "not Send", "Send"])
# # suppressionAutomaton.visualizeAutomaton("No Send after FileRead with Suppression")

# print(output.traceAcceptance)
# print(output.outputTrace)
# print(output.suppressions)