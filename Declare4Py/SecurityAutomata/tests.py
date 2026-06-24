from SecurityAutomataFactory import SecurityAutomataFactory
import os

#Tests and example scenarios for usage of SecurityAutomata package

factory = SecurityAutomataFactory()

# Example 1: No Send after FileRead, Schneider, 2000
# In Declare: Not Response(FileRead, Send)
def example1():
    aut = factory.generateAutomatonFromTemplate("Not Response", ["FileRead", "Send"])
    aut.visualizeAutomaton("No Send after FileRead")

    compliant_input = aut.runTrace(["!FileRead", "FileRead", "!Send", "!Send"])
    print("Compliance: ", compliant_input.traceAcceptance)
    print("Output Trace: ", compliant_input.outputTrace)
    print("Suppressions: ", compliant_input.suppressions,
        " Insertions: ", compliant_input.insertions,
        " Buffer: ", compliant_input.buffer)

    violating_input = aut.runTrace(["!FileRead", "FileRead", "!Send", "Send"])
    print("Compliance: ", violating_input.traceAcceptance)
    print("Output Trace: ", violating_input.outputTrace)
    print("Suppressions: ", violating_input.suppressions,
        " Insertions: ", violating_input.insertions,
        " Buffer: ", violating_input.buffer,
        "Truncations: ", violating_input.truncation)
    
    
# Example 2: Show immediately before board
# Variant of example from Ligatti et al., 2004
# In Declare: ChainPrecedence(Board, Show)
def example2():
    aut = factory.generateAutomatonFromTemplate("Chain Precedence", ["Board", "Show"])
    aut.visualizeAutomaton("Show immediately before Board")
        
    compliant_input = aut.runTrace(["Board", "Show", "Board"])
    print("Compliance: ", compliant_input.traceAcceptance)
    print("Output Trace: ", compliant_input.outputTrace)
    print("Suppressions: ", compliant_input.suppressions,
        " Insertions: ", compliant_input.insertions,
        " Buffer: ", compliant_input.buffer)

    editted_input = aut.runTrace(["Show", "Board", "Board"])
    print("Compliance: ", editted_input.traceAcceptance)
    print("Output Trace: ", editted_input.outputTrace)
    print("Suppressions: ", editted_input.suppressions,
        " Insertions: ", editted_input.insertions,
        " Buffer: ", editted_input.buffer)
         
# Example 3: Atomic payment transactions
# Variant of example from Ligatti et al., 2004
# In Declare: Response(Take, Pay)
def example3():
    aut = factory.generateAutomatonFromTemplate("Response", ["Take", "Pay"])
    aut.visualizeAutomaton("Atomic Payment Transactions")
    
    compliant_input = aut.runTrace(["Take", "Pay", "Take", "Pay"])
    print("Compliance: ", compliant_input.traceAcceptance)
    print("Output Trace: ", compliant_input.outputTrace)
    print("Suppressions: ", compliant_input.suppressions,
        " Insertions: ", compliant_input.insertions,
        " Buffer: ", compliant_input.buffer)

    editted_input = aut.runTrace(["Take", "!Pay", "!Pay"])
    print("Compliance: ", editted_input.traceAcceptance)
    print("Output Trace: ", editted_input.outputTrace)
    print("Suppressions: ", editted_input.suppressions,
        " Insertions: ", editted_input.insertions,
        " Buffer: ", editted_input.buffer)
    
# Example 4: Generate automata from a Declare model file
def example4():
    model_path = os.path.join(os.path.dirname(__file__), "data-model2.decl")
    automata = factory.generateAutomataFromFile(model_path)


    for label, automaton in automata.items():
        automaton.visualizeAutomaton(label)
                
# Example 5: Enforcing complex policies with multiple, simple, security automata
# Uses the composition proposed by Ligatti et al., 2002, where automaton B is run on the output of automaton A, 
# and the output of B is the final output, provided that it does not violate A
# Variant of example from Ligatti et al., 2004
# A passenger must show their ticket before boarding and can only board once
# In Declare: ChainPrecedence(Board, Show) AND AtMostOne(Board)
def example5():
    chainPrecedence = factory.generateAutomatonFromTemplate("Chain Precedence", ["Board", "Show"])
    atMostOne = factory.generateAutomatonFromTemplate("At Most One", ["Board"])
    
    inputA = ["Show", "Board"]
    outputA = chainPrecedence.runTrace(inputA)
    # print(outputA.outputTrace)
    
    inputB = ["!Board" if x != "Board" else x for x in outputA.outputTrace]
    outputB = atMostOne.runTrace(inputB)
    outputB.outputTrace = ["Show" if x == "!Board" else x for x in outputB.outputTrace]
    print("Compliance: ", outputB.traceAcceptance)
    print("Output Trace: ", outputB.outputTrace)
    print("Suppressions: ", outputB.suppressions,
        " Insertions: ", outputB.insertions,
        " Buffer: ", outputB.buffer)
    
    
    inputAEdited = ["Show", "Board", "Board"]
    outputAEdited = chainPrecedence.runTrace(inputAEdited)
    print(outputAEdited.outputTrace)
    
    inputBEdited = ["!Board" if x != "Board" else x for x in outputAEdited.outputTrace]
    outputBEdited = atMostOne.runTrace(inputBEdited)
    outputBEdited.outputTrace = ["Show" if x == "!Board" else x for x in outputBEdited.outputTrace]
    print("Compliance: ", outputBEdited.traceAcceptance)
    print("Output Trace: ", outputBEdited.outputTrace)
    print("Suppressions: ", outputBEdited.suppressions,
        " Insertions: ", outputBEdited.insertions,
        " Buffer: ", outputBEdited.buffer)
example2()

    
    