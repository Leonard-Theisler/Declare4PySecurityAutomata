from typing import Dict, List, Tuple

class TruncationAutomaton:
    
    def __init__(self, initial_state: str,
                 states: List[str],
                 transitions: dict[Tuple[str,str], str]):
        
        self._initial_state: str= initial_state
        self._states = states
        self._transitions = transitions

        self.currentState: str = None
        self.outputTrace: List[str] = None


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
        for action in trace:
            if not self.canExecuteAction(action):
                print("The action ", action, "is a violation of the security policy. The automaton has truncated the execution.")
                break
            self.fireTransition(action)

        print("The output trace is: ")
        for action in self.outputTrace:
            print(action)

