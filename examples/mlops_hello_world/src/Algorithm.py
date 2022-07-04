from Algorithmia import ADK
from time import time

# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def load(state):
    # Lets initialize the final components of the MLOps plugin and prepare it for sending info back to DataRobot.
    state['mlops'] = MLOps().init()
    return state

def apply(input, state):
    t1 = time()
    df = pd.DataFrame(columns=['id', 'values'])
    df.loc[0] = ["abcd", 0.25]
    df.loc[0][1] += input
    association_ids = df.iloc[:, 0].tolist()
    reporting_predictions = df.loc[0][1]
    t2 = time()
    # As we're only making 1 prediction, our reporting tool should show only 1 prediction being made
    state['mlops'].report_deployment_stats(1, t2 - t1)

    # Report the predictions data: features, predictions, class_names
    state['mlops'].report_predictions_data(features_df=df,
                                           predictions=reporting_predictions,
                                           association_ids=association_ids)
    return reporting_predictions


algorithm = ADK(apply, load)
algorithm.init(0.25, mlops=True)

