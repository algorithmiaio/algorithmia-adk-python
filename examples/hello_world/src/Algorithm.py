from adk import ADK


def apply(input):
    return "hello {}".format(str(input))


algorithm = ADK(apply)
algorithm.serve()