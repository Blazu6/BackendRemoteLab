INST_TERM = ";"
ARG_SEP = "."
EL_SEP = ","


def _check_arg(elem: str) -> str:
    if elem.endswith(INST_TERM):
        elem = elem[:-1]
    elem_length, elem_data = elem.split(ARG_SEP, 1)
    if len(elem_data) != int(elem_length):
        raise ValueError(f"Invalid Guacamole protocol message {elem}")

    return elem_data


def _encode_element(elem: str) -> str:
    return f"{len(elem)}{ARG_SEP}{elem}"


class GuacamoleProtocol:
    def __init__(self, opcode, *args):
        self.opcode = opcode
        self.args = args

    def __repr__(self):
        return f"GuacamoleProtocol(opcode={self.opcode!r}, args={self.args!r})"


    @classmethod
    def decode(cls, instruction: str):
        if not instruction.endswith(INST_TERM):
            raise ValueError("Instruction termination not found")
        args = [_check_arg(arg) for arg in instruction.split(EL_SEP)]
        opcode = args[0]
        rest_args = args[1:]

        return cls (opcode, *rest_args)
        

    def encode(self):
        parts = [_encode_element(self.opcode)] + [_encode_element(a) for a in self.args]
        elems = EL_SEP.join(parts) + INST_TERM

        return elems



if __name__ == "__main__":
    p = GuacamoleProtocol("connect", "127.0.0.1", "22")
    print(p.encode())
    print(p.decode("7.connect,9.127.0.0.1,2.22;"))
