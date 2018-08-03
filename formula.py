# formula:  module for safe formula evaluation.  (C) 2018, Opsani.
import math

def get_gbl():
    '''
    return a dict with set of globals to be passed as environment for the evaluation
    This includes selected built-in functions and the math functions/constants.

    Note: unless the returned dict has a __builtins__ element, Python will include
          all globals! see https://docs.python.org/3/library/functions.html#eval
    '''
    # create a safe and desirable subset of the built-ins
    builtins = {'abs':abs, 'bool':bool, 'float':float, 'int':int, 'len':len,
        'list':list, 'map':map, 'max':max, 'min':min, 'pow':pow, 'round':round,
        'set':set, 'sum':sum, 'True':True, 'False':False, 'None':None, 'str':str
    }

    # create a full set of usable math functions and constants
    maths = { x:getattr(math,x) for x in dir(math) if not x.startswith('_') }

    # return all; order matters (see https://www.python.org/dev/peps/pep-0448/)
    # see docstring above re __builtins__
    return { '__builtins__' : builtins, **maths }

def evaluate(expr, var):
    '''
    Safely evaluate an expression from user-defined string, using pre-defined
    library functions (incl. all the useful math functions/const) and symbolic
    variables.

    Args:
        expr: string containing the expression to evaluate (e.g., 'perf*2/cost')
        var: dict with zero or more variables to use (e.g., {'perf':2000,'cost':0.02})

    The evaluation supports constants, all Python operators as well as a select
    subset of safe Python built-ins and the full math module (not prefixed by 'math.')

    Note that vars will shadow any of the standard const/funcs, e.g., if a var 'pi'
    is included in the vars arg, it will shadow the standard math.pi value.
    '''
    ret = eval(expr, get_gbl(), var)
    return ret
