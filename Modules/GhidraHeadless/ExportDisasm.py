# ExportDisasm.py
#@category Export

out_path = getScriptArgs()[0]

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()

with open(out_path, "w") as f:
    funcs = fm.getFunctions(True)

    for func in funcs:
        f.write("FUNCTION %s %s\n" % (func.getName(), func.getEntryPoint()))

        insn = listing.getInstructionAt(func.getEntryPoint())
        while insn is not None:
            addr = insn.getAddress()

            if not func.getBody().contains(addr):
                break

            num_ops = insn.getNumOperands()
            ops = []
            for i in range(num_ops):
                ops.append(insn.getDefaultOperandRepresentation(i))

            operand_text = ", ".join(ops)

            if operand_text:
                f.write("0x%s: %s %s\n" % (
                    addr.toString(),
                    insn.getMnemonicString(),
                    operand_text
                ))
            else:
                f.write("0x%s: %s\n" % (
                    addr.toString(),
                    insn.getMnemonicString()
                ))

            insn = insn.getNext()

        f.write("\n")