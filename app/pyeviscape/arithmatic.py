from __future__ import division

# Uncomment the line below for readline support on interactive terminal
# import readline  
import re
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral \
, Combine, Optional, nums, Or, Forward, ZeroOrMore, StringEnd, alphanums
import math

CONSTS = {
    'g': (9.80665, 'gravitational acceleration',  'm/s<sup>2</sup>'),
    'c': (299792458e-0, 'speed of light', 'm/s'),
    'G': (6.67300e-11, 'gravitational constant', 'm<sup>3</sup>kg<sup>-1</sup>s<sup>-2</sup>'),
    'h': (6.62606896e-34, "Planck's constant", 'm<sup>2</sup>kg/s')
}

exprStack = []
varStack  = []

# map operator symbols to corresponding arithmetic operations
opn = { "+" : ( lambda a,b: a + b ),
        "-" : ( lambda a,b: a - b ),
        "*" : ( lambda a,b: a * b ),
        "/" : ( lambda a,b: a / b ),
        "^" : ( lambda a,b: a ** b ),
        "%" : ( lambda a,b: a % b )}

class ComputationException(Exception):
    pass



def append_to_list(list, str):
    for i in list:
        if i == str:
            return
    list.append(str)
    

def pushFirst( str, loc, toks ):
    exprStack.append( toks[0] )

def assignVar( str, loc, toks ):
    varStack.append( toks[0] )

# Recursive function that evaluates the stack
def evaluateStack( s, explain_list):
    op = s.pop()
    if op in "+-*/^":
        op2 = evaluateStack( s, explain_list )
        op1 = evaluateStack( s, explain_list )
        return opn[op]( op1, op2 )
    elif op == "pi" or op == 'PI':
        return math.pi
    elif op == "e":
        return math.e
    elif re.search('^[a-zA-Z][a-zA-Z0-9_]*$',op):
        if CONSTS.has_key(op):
            append_to_list(explain_list, "%s is %s in %s" % (op, CONSTS[op][1], CONSTS[op][2]))
            return CONSTS[op][0]
        else:
            raise ComputationException, "Error while computing"
    elif re.search('^[-+]?[0-9]+$',op):
        return long( op )
    else:
        return float( op )



def compute(input_string):
    # Debugging flag can be set to either "debug_flag=True" or "debug_flag=False"
    debug_flag=False
    
    explain_list = []
    variables = {}



    # define grammar
    point = Literal('.')
    e = CaselessLiteral('E')
    plusorminus = Literal('+') | Literal('-')
    number = Word(nums) 
    integer = Combine( Optional(plusorminus) + number )
    floatnumber = Combine( integer +
                           Optional( point + Optional(number) ) +
                           Optional( e + integer )
                         )
    
    ident = Word(alphas,alphanums + '_') 
    
    plus  = Literal( "+" )
    minus = Literal( "-" )
    mult  = Literal( "*" )
    div   = Literal( "/" )
    lpar  = Literal( "(" ).suppress()
    rpar  = Literal( ")" ).suppress()
    addop  = plus | minus
    multop = mult | div
    expop = Literal( "^" )
    assign = Literal( "=" )
    
    expr = Forward()
    atom = ( ( e | floatnumber | integer | ident ).setParseAction(pushFirst) | 
             ( lpar + expr.suppress() + rpar )
           )
            
    factor = Forward()
    factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )
            
    term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
    expr << term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )
    bnf = Optional((ident + assign).setParseAction(assignVar)) + expr
    
    pattern =  bnf + StringEnd()

    if input_string != '':
        try:
            L=pattern.parseString( input_string )
        except ParseException,err:
            raise ComputationException, "Error while parsing"
        print exprStack
        if len(exprStack) <= 1:
            return None
        result=evaluateStack(exprStack, explain_list)
        if len(str(result)) > 12:
            ret = "%e" % result
        else:
            ret = str(result)
        ret = ret.replace('e', ' x 10^')
        ret = ret.replace('+', '')
        if len(explain_list):
            return "%s (%s)" %(ret, ", ".join(explain_list))
        else:
            return "%s" % ret
