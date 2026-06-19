from typing import List, Tuple
from enum import Enum

class TraceAcceptance(Enum):
    VALID = 0
    BUFFERED = 1
    EDITTED = 2
    HALTED = 3
    
    
class OutputSequence:
    
    def __init__(self):
        self.outputTrace: List[str] = []
        self.traceAcceptance: TraceAcceptance = TraceAcceptance.VALID.name
        self.suppressions: List[Tuple[str, str, str]] = [] #(action, state, position)
        self.insertions: List[Tuple[List[str], str, str]] = [] #(actions, state, position)
        self.truncation: Tuple[str, str, str] = ("", "", "") #(action, state, position)
        self.buffer: List[List[str]] = []
        
    def addSuppression(self, action, state, position):
        self.suppressions.append((action, state, position))
        self.computeTraceAcceptance()
        
    def addInsertion(self, actions, state, position):
        self.insertions.append((actions, state, position))
        self.computeTraceAcceptance()

    
    def addTuncation(self, action, state, position):
        self.truncation = (action, state, position)
        self.traceAcceptance = TraceAcceptance.HALTED.name
        
    def computeTraceAcceptance(self):
        for act, state, pos in self.insertions:
            if act == "buffer":
                self.traceAcceptance = TraceAcceptance.BUFFERED.name
                return
        for suppression in self.suppressions:
            for actions, state, pos in self.insertions:
                if suppression[0] in actions and suppression[2] == pos-1 and len(actions) == 1:
                    self.traceAcceptance = TraceAcceptance.BUFFERED.name
                    return
        self.traceAcceptance = TraceAcceptance.EDITTED.name
        
    def addBuffer(self, buffer):
        self.buffer.append(list(buffer))