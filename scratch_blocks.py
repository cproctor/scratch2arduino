import re
import json
from random import randint

# Define: 
#   blocks are sequences of statements that stick together.
#   statements are represented by vertical levels in a script.
#   expressions are within statements, and evaluate to a value.

def clean_name(name):
    "Converts a name to a canonical form"
    name = name.lower()
    name = re.sub('%n', '', name)
    name = name.strip()
    name = re.sub('\s+', '_', name)
    name = re.sub('[^a-zA-Z_]', '', name)
    return name

class BlockNotSupportedError(Exception):
    pass

class ScratchRepresentation(object):
    arduino_rep = "(Representation of Scratch code)"
    indent=0
    indent_chars = " " * 4
    def __init__(self, rep_json):
        self.parse(rep_json)
    def parse(self, rep_json):
        pass
    def __repr__(self):
        return self.to_arduino()
    def __str__(self):
        return "<ScratchRepresentation>"
    def to_arduino(self):
        return self.arduino_rep.format(*self.__dict__)
    def indented(self, string):
        return "{}{}".format(self.indent_chars * self.indent, string)

class ScratchScript(ScratchRepresentation):

    def __init__(self, script_json, indent=0, namespace=None):
        print("Parsing: {}".format(script_json))
        self.indent = indent
        self.name = None
        self.parse(script_json)
        print("Parsed script {}".format(self.name))

    def __str__(self):
        return "<ScratchScript {}>".format(self.name)
    def __repr__(self):
        return "<ScratchScript {}>".format(self.name)

    def parse(self, script_json):
        pass

    def to_arduino(self):
        return self.indented("(SCRIPT)")
        
    @classmethod
    def instantiate(cls, script_json):
        return cls.identify(script_json)(script_json)

    @classmethod
    def identify(cls, script_json):
        x, y, block_json = script_json
        signature = block_json[0]
        try:
            return SCRIPT_IDENTIFIERS[signature[0]]
        except KeyError:
            raise BlockNotSupportedError(
                    "Scripts of type {} are not supported".format(signature[0]))

class NullScript(ScratchScript):
    def to_arduino(self):
        "(NULL SCRIPT)"

class Function(ScratchScript):

    def __init__(self, script_json, indent=0, namespace=None, signature=None):
        self.indent = indent
        if signature:
            self.signature = signature
        self.parse(script_json)

    def __str__(self):
        return "<Function {}>".format(self.name)

    def parse(self, script_json):
        x, y, block_json = script_json
        if hasattr(self, "signature"):
            self.name = self.signature['name']
            self.arg_names = self.signature['arg_names']
            self.arg_types = self.signature['arg_types']
        else:
            signature_json = block_json[0]
            _, self.name, self.arg_names, self.arg_types, _ = signature_json
            self.name = clean_name(self.name)
            self.arg_names = [clean_name(arg) for arg in self.arg_names]
        description_json = block_json[1:]
        self.block = ScratchCodeBlock(description_json, indent=self.indent + 1)

    def to_arduino(self):
        return "\n".join([
            self.indented("void {} ({}) {{".format(self.name, self.args_to_arduino())),
            self.block.to_arduino(),
            self.indented("}")
        ])

    def args_to_arduino(self):
        def arduino_type(symbol):
            if symbol == 1:
                return "int"
            else:
                raise BlockNotSupportedError(
                        "Functions with arg type {} are not yet supported".format(symbol))
        arduino_args = []
        for i, arg in enumerate(self.arg_names):
            arduino_args.append("{} {}".format(
                arduino_type(self.arg_types[i]),
                arg
            ))
        return ", ".join(arduino_args)

class EventBinding(ScratchScript):
    def parse(self, script_json):
        x, y, block_json = script_json
        signature_json = block_json[0]
        self.fn_name = self.get_fn_name(signature_json)
        self.name = "Event binding for {}".format(self.event_name)
        self.fn = Function(script_json, indent=self.indent, signature={
            "name": self.fn_name,
            "arg_names": [],
            "arg_types": []
        })

    def get_fn_name(self, signature_json):
        print("GET FN NAME: {}".format(signature_json))
        identifier, self.event_name = signature_json
        self.event_name = clean_name(self.event_name)
        self.fn_id = randint(0, 100000)
        self.fn_name = "{}_function_{}".format(self.event_name, self.fn_id)
        
    def to_arduino(self):
        return "\n".join([
            self.fn.to_arduino(),
            self.indented("dispatcher.bind({}, {});".format(self.event_name, self.fn_name))
        ])

    def __str__(self):
        return "<EventBinding {} -> {}>".format(self.event_name, self.fn_name)

class GreenFlag(EventBinding):
    def get_fn_name(self, signature_json):
        self.event_name = "green_flag"
        self.fn_id = randint(0, 100000)
        self.fn_name = "{}_function_{}".format(self.event_name, self.fn_id)

class ScratchCodeBlock(ScratchRepresentation):
    "Represents a code block: a list of statements"

    def __init__(self, code_block_json, indent=0):
        self.indent = indent
        self.statements = [ScratchStatement.instantiate(st, indent=self.indent) for st in code_block_json]
            
    def to_arduino(self):
        statement_representations = [s.to_arduino() for s in self.statements]
        statement_reps = filter(lambda x: x, statement_representations)
        return "\n".join(statement_representations)

class ScratchStatement(ScratchRepresentation):
    "Represents one line in a Scratch script, including any nested blocks"
    arduino_rep = "(STATEMENT)"

    def __init__(self, statement_json, indent=0):
        self.indent = indent
        self.parse(statement_json)

    def to_arduino(self):
        return self.indented(self.arduino_rep.format(*self.__dict__))

    @classmethod
    def instantiate(cls, statement_json, indent=0):
        "Returns an instance of the appropriate class"
        return cls.identify(statement_json)(statement_json, indent=indent)

    @classmethod
    def identify(cls, statement_json):
        "Given valid JSON for a statement, will return the appropriate class"
        try:
            identifier = statement_json[0]
            return STATEMENT_IDENTIFIERS[identifier]
        except KeyError:
            raise BlockNotSupportedError("No statement matches {}".format(identifier))

class SetVar(ScratchStatement):
    def parse(self, statement_json):
        self.var_name = clean_name(statement_json[1])
        self.set_value = ScratchExpression.instantiate(statement_json[2])
    def to_arduino(self):
        return self.indented(
            "{} = {};".format(self.var_name, self.set_value.to_arduino())
        )

class ChangeVarBy(ScratchStatement):
    def parse(self, statement_json):
        self.var_name = clean_name(statement_json[1])
        self.change_value = ScratchExpression.instantiate(statement_json[2])
    def to_arduino(self):
        return self.indented(
            "{} = {} + {};".format(self.var_name, self.var_name, self.change_value.to_arduino())
        )

class SetListItemValue(ScratchStatement):
    def parse(self, statement_json):
        self.index = ScratchExpression.instantiate(statement_json[1])
        self.array_name = clean_name(statement_json[2])
        self.value = ScratchExpression.instantiate(statement_json[3])

    def to_arduino(self):
        return self.indented("{}[{}] = {};".format(self.array_name, 
                self.index.to_arduino(), self.value.to_arduino()))

class Broadcast(ScratchStatement):
    # TODO It will be necessary to provide a dispatcher!

    def parse(self, statement_json):
        self.broadcast_token = clean_name(statement_json[1])

    def to_arduino(self):
        return  self.indented(
            "dispatcher.broadcast({});".format(self.broadcast_token)
        )

class Wait(ScratchStatement):
    def parse(self, statement_json):
        self.duration = ScratchExpression.instantiate(statement_json[1])
    def to_arduino(self):
        return self.indented("delay({});".format(self.duration * 1000))


class DoIf(ScratchStatement):
    def parse(self, statement_json):
        self.condition = ScratchExpression.instantiate(statement_json[1])
        self.block = ScratchCodeBlock(statement_json[2], indent=self.indent+1)
    def to_arduino(self):
        return "\n".join([
            self.indented("if ({}) {{".format(self.condition.to_arduino())),
            self.block.to_arduino(),
            self.indented("}")
        ])

class DoIfElse(ScratchStatement):
    def parse(self, statement_json):
        self.condition = ScratchExpression.instantiate(statement_json[1])
        self.if_block = ScratchCodeBlock(statement_json[2], indent=self.indent+1)
        self.else_block = ScratchCodeBlock(statement_json[3], indent=self.indent+1)
    def to_arduino(self):
        return "\n".join([
            self.indented("if ({}) {{".format(self.condition.to_arduino())),
            self.if_block.to_arduino(),
            self.indented("} else {"),
            self.else_block.to_arduino(),
            self.indented("}")
        ])

class DoRepeat(ScratchStatement):
    def parse(self, statement_json):
        self.repeats = ScratchExpression.instantiate(statement_json[1])
        self.block = ScratchCodeBlock(statement_json[2], indent=self.indent+1)
        self.counter_name = "counter_{}".format(randint(0,100000))

    def to_arduino(self):
        return "\n".join([
            self.indented("for (int {} = 0; {} < {}; {}++;) {{".format(self.counter_name, 
                    self.counter_name, self.repeats, self.counter_name)),
            self.block.to_arduino(),
            self.indented("}")
        ])

class DoForever(ScratchStatement):
    def parse(self, statement_json):
        self.block = ScratchCodeBlock(statement_json[1], indent=self.indent+1)
    def to_arduino(self):
        return "\n".join([
            self.indented("while (true) {"),
            self.block.to_arduino(),
            self.indented("}")
        ])
        
class ScratchExpression(ScratchRepresentation):
    """ Represents an expression that evaluates to a number, string, or boolean. 
    In Scratch, these will be shaped as hexagons or rounded rectangles.    """

    arduino_rep = "(EXPRESSION)"

    @classmethod
    def instantiate(cls, exp_json):
        return cls.identify(exp_json)(exp_json)

    @classmethod
    def identify(cls, exp_json):
        if isinstance(exp_json, basestring):
            if exp_json.isdigit():
                return LiteralNumber
            else:
                return LiteralString
        elif isinstance(exp_json, (int, float)):
            return LiteralNumber
        else:
            try:
                identifier = exp_json[0]
                return EXPRESSION_IDENTIFIERS[identifier]
            except KeyError:
                raise BlockNotSupportedError("No expression matches {}".format(identifier))

class Literal():
    def parse(self, value):
        self.value = value
    def to_arduino(self):
        return json.dumps(self.value)

class LiteralString(ScratchExpression):
    def parse(self, value):
        self.value = value
    def to_arduino(self):
        return json.dumps(self.value)

class LiteralNumber(ScratchExpression):
    def parse(self, value):
        self.value = int(value)
    def to_arduino(self):
        return json.dumps(self.value)

class BinaryOperator(ScratchExpression):
    operator = "(SYMBOL)"
    def parse(self, exp_json):
        self.arg1 = ScratchExpression.instantiate(exp_json[1])
        self.arg2 = ScratchExpression.instantiate(exp_json[2])

    def to_arduino(self):
        return "({} {} {})".format(self.arg1.to_arduino(), self.operator, 
                self.arg2.to_arduino())

class Equals(BinaryOperator):
    operator = "=="

class Add(BinaryOperator):
    operator = "+"

class Subtract(BinaryOperator):
    operator = "-"

class Multiply(BinaryOperator):
    operator = "*"

class Divide(BinaryOperator):
    operator = "/"

class Modulo(BinaryOperator):
    operator = "%"

class GreaterThan(BinaryOperator):
    operator = ">"

class LessThan(BinaryOperator):
    operator = "<"

class ReadVar(ScratchExpression):
    def __init__(self, exp_json, namespace=None):
        self.varName = clean_name(exp_json[1])
        if namespace and self.varName not in namespace:
            raise ValueError("{} is not a variable in {}".format(
                    self.varName, namespace))

    def to_arduino(self):
        return self.varName

class KeyPressed(ScratchExpression):
    "NOT REALLY SUPPORTED"
    def parse(self, exp_json):
        self.key = exp_json[1]

    def to_arduino(self):
        return '(false == "{} KEY PRESSED")'.format(self.key)
        

class GetParam(ScratchExpression):
    def __init__(self, exp_json, namespace=None):
        self.varName = clean_name(exp_json[1])
        if namespace and self.varName not in namespace:
            raise ValueError("{} is not a parameter in {}".format(
                    self.varName, namespace))

    def to_arduino(self):
        return self.varName

class Call(ScratchStatement):
    def parse(self, statement_json):
        self.function_name = clean_name(statement_json[1])
        self.args = [ScratchExpression.instantiate(arg) for arg in statement_json[2:]]

    def to_arduino(self):
        arduino_args = [arg.to_arduino() for arg in self.args]
        return self.indented(
                "{}({});".format(self.function_name, ", ".join(arduino_args))
        )

class NullStatement(ScratchStatement):
    def to_arduino(self):
        return None

BLOCK_IDENTIFIERS = {
    # 'procDef'   : Function,
#    '='         : OpEq,
#    '>'         : OpGt,
#    '<'         : OpLt,
#    '+'         : OpPlus,
#    '-'         : OpMinus,
#    '*'         : OpTimes,
#    '/'         : OpDiv,
#    '%'         : OpMod,
#    'getParam'  : ParamGet,
#    'readVariable': VarGet,
}
            
STATEMENT_IDENTIFIERS = {
    'doIf'      : DoIf,
    'doRepeat'  : DoRepeat,
    'doForever' : DoForever,
    'call'      : Call,
    'doIfElse'  : DoIfElse,
    'setVar:to:': SetVar,
    'changeVar:by:': ChangeVarBy,
    'setLine:ofList:to:': SetListItemValue,
    'broadcast:': Broadcast,
    'wait:elapsed:from:': Wait,

    # These have effects that don't map to Arduino
    # Currently, we just trash them.
    'hide'          : NullStatement,
    "createCloneOf" : NullStatement,
    "doWaitUntil"   : NullStatement,
    "lookLike:"     : NullStatement,
    "setGraphicEffect:to:" : NullStatement,
    "gotoX:y:"      : NullStatement,
    
    # Can't do these properly yet.
    # Need to fake dynamic arrays...
    "deleteLine:ofList:" : NullStatement,
    "append:toList:"     : NullStatement,
}

EXPRESSION_IDENTIFIERS = {
    "="             : Equals,
    "+"             : Add,
    "-"             : Subtract,
    "*"             : Multiply,
    "/"             : Divide,
    "%"             : Modulo,
    ">"             : GreaterThan,
    "<"             : LessThan,
    "readVariable"  : ReadVar,
    "getParam"      : GetParam,
    "keyPressed:"   : KeyPressed
}

SCRIPT_IDENTIFIERS = {
    "procDef"       : Function,
    "whenIReceive"  : EventBinding,
    "whenGreenFlag" : GreenFlag,
    "createCloneOf" : NullScript,
    "whenCloned"    : NullScript,
    "think:"    : NullScript
}
            
