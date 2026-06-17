from fileinput import filename
from typing import Dict, List, Tuple

import graphviz
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
            for action in trace:
                if not self.canExecuteAction((action, self.currentState)):
                    print("The action ", action, "is a violation of the security policy. The automaton has truncated the execution.")
                    break
                elif self.suppressAction((action, self.currentState)):
                    self.fireSuppressedTransition((action, self.currentState))
                    print("Suppressed action: ", action)
                else:
                    self.fireTransition((action, self.currentState))

            print("The output trace is: ")
            for action in self.outputTrace:
                print(action)
                
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
                
#suppressionAutomaton = SuppressionAutomaton("Qnfr", ["Qnfr", "Qfr"], {("not FileRead", "Qnfr"): "Qnfr", ("FileRead", "Qnfr"): "Qfr", ("not Send", "Qfr"): "Qfr", ("Send", "Qfr"): "Qfr"}, {("not FileRead", "Qnfr"): "+", ("FileRead", "Qnfr"): "+", ("not Send", "Qfr"): "+", ("Send", "Qfr"): "-"})
#suppressionAutomaton.runTrace(["not FileRead", "FileRead", "not Send", "Send"])
#suppressionAutomaton.visualizeAutomaton("No Send after FileRead with Suppression")
                    