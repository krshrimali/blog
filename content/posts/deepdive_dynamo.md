## Notes

**Deepdive of Torch Dynamo**

Problem: Python code - many tensor operations - somehow extract out the graph of ops in question - to be passed to compiler.
Problems with eager mode: compile graphs together into single ops, need to leverage accelerator's potential.

How does TorchDynamo solve the problem?

- Frame evaluation API - was added to Python to support JIT
- Python parsed into Byte code -> byte code runs in interpreter loop in CPython
- Byte code: simplified 
- Frame evaluation API, instead of passing bytecode to CPython - you can pass it to your call back and modify the bytecode if you wish. Or even make it to compiled object code
- Generate bytecode -> do some analysis on it (symbolically evaluate the byte code) - this will give us all the tensor operations.

- Question: how do you deal with CPython changing it's bytecode set?
- Answer: We have to update TorchDynamo every time there is a new CPython's version.

Note: TorchDynamo doesn't have support for generators.
