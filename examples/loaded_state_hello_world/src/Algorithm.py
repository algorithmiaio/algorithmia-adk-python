from Algorithmia import ADK
import Algorithmia

# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def apply(input, globals):
    # If your apply function uses state that's loaded into memory via load, you can pass that loaded state to your apply
    # function by defining an additional "globals" parameter in your apply function.
    return "hello {} {}".format(str(input), str(globals['payload']))


def load():
    # Here you can optionally define a function that will be called when the algorithm is loaded.
    # The return object from this function can be passed directly as input to your apply function.
    # A great example would be any model files that need to be available to this algorithm
    # during runtime.

    # Any variables returned here, will be passed as the secondary argument to your 'algorithm' function
    globals = {}
    globals['payload'] = "Loading has been completed."
    return globals

def handle_exceptions(exp):
    # Additionally, if you plan to ship failure or metric information critical to your business to an aggregation
    # service using Algorithmia insights or a third party solution; it's recommended to implement this function. This
    # function takes 2 inputs parameters; the exception and  and returns nothing. If any exceptions are detected; you
    # can process them here. This reduces the need to use built-in try/catch logic, which reduces the chances for
    # catching the wrong error!
    client = Algorithmia.client()
    client.report_insights({"exception": str(exp)})


# This turns your library code into an algorithm that can run on the platform.
# If you intend to use loading operations, remember to pass a `load` function as a second variable.
algorithm = ADK(apply, load, handle_exceptions)
# The 'init()' function actually starts the algorithm, you can follow along in the source code
# to see how everything works.
algorithm.init("Algorithmia")
