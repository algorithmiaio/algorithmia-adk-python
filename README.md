# Algorithm Development Kit (ADK), Python edition

<!-- embedme examples/hello_world/src/Algorithm.py -->
```python
from Algorithmia import ADK


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def apply(input):
    # If your apply function uses state that's loaded into memory via load, you can pass that loaded state to your apply
    # function by defining an additional "globals" parameter in your apply function; but it's optional!
    return "hello {}".format(str(input))


# This turns your library code into an algorithm that can run on the platform.
# If you intend to use loading operations, remember to pass a `load` function as a second variable.
algorithm = ADK(apply)
# The 'init()' function actually starts the algorithm, you can follow along in the source code
# to see how everything works.
algorithm.init("Algorithmia")

```
## Focus
This document will describe the following:
- What is an Algorithm Development Kit
- Changes to Algorithm development
- Example workflows you can use to create your own Algorithms.
- The Model Manifest System
- Datarobot MLOps integrations support


## What is an Algorithm Development Kit
An Algorithm Development Kit is a package that contains all of the necessary components to convert a regular application into one that can be executed and run on Algorithmia.
To do that, an ADK must be able to communicate with [langserver](https://github.com/algorithmiaio/langpacks/blob/develop/langpack_guide.md).
To keep things simple, an ADK exposes some optional functions, along with an `apply` function that acts as the explicit entrypoint into your algorithm.
Along with those basics, the ADK also exposes the ability to execute your algorithm locally, without `langserver`; which enables better debuggability.

![adk architecture](assets/adk_architecture.png)

This kit, when implemented by an algorithm developer - enables an easy way to get started with your project, along with well defined hooks to integrate with an existing project.


## Changes to Algorithm Development

Algorithm development does change with this introduction:
- Primary development file has been renamed to `src/Algorithm.py` to aide in understanding around what this file actually does / why it's important
- An additional import (`from algorithm import ADK`)
- An optional `load()` function that can be implemented
    - This enables a dedicated function for preparing your algorithm for runtime operations, such as model loading, configuration, etc
- A call to the handler function with your `apply` and optional` load` functions as inputs
    - ```python
      algorithm = ADK(apply)
      algorithm.init("Algorithmia")
      ```
    - Converts the project into an executable, rather than a library
      - Which will interact with the `langserver` service on Algorithmia
      - But is debuggable via stdin/stdout when executed locally / outside of an Algorithm container
        - When a payload is provided to `init()`, that payload will be directly provided to your algorithm when executed locally, bypassing stdin parsing and simplifying debugging!
      - This includes being able to step through your algorithm code in your IDE of choice! Just execute your `src/Algorithm.py` script and try stepping through your code with your favorite IDE

## Example workflows
Check out these examples to help you get started:
### [hello world example](examples/hello_world)
  <!-- embedme examples/hello_world/src/Algorithm.py -->
```python
from Algorithmia import ADK


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def apply(input):
    # If your apply function uses state that's loaded into memory via load, you can pass that loaded state to your apply
    # function by defining an additional "globals" parameter in your apply function; but it's optional!
    return "hello {}".format(str(input))


# This turns your library code into an algorithm that can run on the platform.
# If you intend to use loading operations, remember to pass a `load` function as a second variable.
algorithm = ADK(apply)
# The 'init()' function actually starts the algorithm, you can follow along in the source code
# to see how everything works.
algorithm.init("Algorithmia")

```

### [hello world example with loaded state](examples/loaded_state_hello_world)
<!-- embedme examples/loaded_state_hello_world/src/Algorithm.py -->
```python
from Algorithmia import ADK


# API calls will begin at the apply() method, with the request body passed as 'input'
# For more details, see algorithmia.com/developers/algorithm-development/languages

def apply(input, modelData):
    # If your apply function uses state that's loaded into memory via load, you can pass that loaded state to your apply
    # function by defining an additional "globals" parameter in your apply function.
    return "hello {} {}".format(str(input), str(modelData.user_data['payload']))


def load(modelData):
    # Here you can optionally define a function that will be called when the algorithm is loaded.
    # The return object from this function can be passed directly as input to your apply function.
    # A great example would be any model files that need to be available to this algorithm
    # during runtime.

    # Any variables returned here, will be passed as the secondary argument to your 'algorithm' function
    modelData['payload'] = "Loading has been completed."
    return modelData


# This turns your library code into an algorithm that can run on the platform.
# If you intend to use loading operations, remember to pass a `load` function as a second variable.
algorithm = ADK(apply, load)
# The 'init()' function actually starts the algorithm, you can follow along in the source code
# to see how everything works.
algorithm.init("Algorithmia")

```
## [pytorch based image classification](examples/pytorch_image_classification)
<!-- embedme examples/pytorch_image_classification/src/Algorithm.py -->
```python
from Algorithmia import ADK
import Algorithmia
import torch
from PIL import Image
import json
from torchvision import models, transforms


client = Algorithmia.client()

def load_labels(label_path):
    with open(label_path) as f:
        labels = json.load(f)
    labels = [labels[str(k)][1] for k in range(len(labels))]
    return labels


def load_model(model_path):
    model = models.squeezenet1_1()
    weights = torch.load(model_path)
    model.load_state_dict(weights)
    return model.float().eval()


def get_image(image_url, smid_algo, client):
    input = {"image": image_url, "resize": {"width": 224, "height": 224}}
    result = client.algo(smid_algo).pipe(input).result["savePath"][0]
    local_path = client.file(result).getFile().name
    img_data = Image.open(local_path)
    return img_data


def infer_image(image_url, n, globals):
    model = globals["model"]
    labels = globals["labels"]
    image_data = get_image(image_url, globals["SMID_ALGO"], globals["CLIENT"])
    transformed = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])])
    img_tensor = transformed(image_data).unsqueeze(dim=0)
    infered = model.forward(img_tensor)
    preds, indicies = torch.sort(torch.softmax(infered.squeeze(), dim=0), descending=True)
    predicted_values = preds.detach().numpy()
    indicies = indicies.detach().numpy()
    result = []
    for i in range(n):
        label = labels[indicies[i]].lower().replace("_", " ")
        confidence = float(predicted_values[i])
        result.append({"label": label, "confidence": confidence})
    return result


def load(modelData):

    modelData["SMID_ALGO"] = "algo://util/SmartImageDownloader/0.2.x"
    modelData["model"] = load_model(modelData.get_model("squeezenet"))
    modelData["labels"] = load_labels(modelData.get_model("labels"))
    return modelData


def apply(input, modelData):
    if isinstance(input, dict):
        if "n" in input:
            n = input["n"]
        else:
            n = 3
        if "data" in input:
            if isinstance(input["data"], str):
                output = infer_image(input["data"], n, modelData)
            elif isinstance(input["data"], list):
                for row in input["data"]:
                    row["predictions"] = infer_image(row["image_url"], n, modelData)
                output = input["data"]
            else:
                raise Exception("\"data\" must be a image url or a list of image urls (with labels)")
            return output
        else:
            raise Exception("\"data\" must be defined")
    else:
        raise Exception("input must be a json object")


algorithm = ADK(apply_func=apply, load_func=load, client=client)
algorithm.init({"data": "https://i.imgur.com/bXdORXl.jpeg"})

```

## The Model Manifest System
Model Manifests are optional files that you can provide to your algorithm to easily
define important model files, their locations; and metadata - this file is called `model_manifest.json`.
<!-- embedme examples/pytorch_image_classification/model_manifest.json -->
```json
{
  "required_files" : [
      { "name": "squeezenet",
      "source_uri": "data://AlgorithmiaSE/image_cassification_demo/squeezenet1_1-f364aa15.pth",
      "fail_on_tamper": true,
      "metadata": {
        "dataset_md5_checksum": "46a44d32d2c5c07f7f66324bef4c7266"
      }
    },
    {
      "name": "labels",
      "source_uri": "data://AlgorithmiaSE/image_cassification_demo/imagenet_class_index.json",
      "fail_on_tamper": true,
      "metadata": {
        "dataset_md5_checksum": "46a44d32d2c5c07f7f66324bef4c7266"
      }
    }
  ],
  "optional_files": [
      {
        "name": "mobilenet",
        "source_uri": "data://AlgorithmiaSE/image_cassification_demo/mobilenet_v2-b0353104.pth",
        "fail_on_tamper": false,
        "metadata": {
            "dataset_md5_checksum": "46a44d32d2c5c07f7f66324bef4c7266"
          }
      }
  ]
}
```
With the Model Manifest system, you're also able to "freeze" your model_manifest.json, creating a model_manifest.json.freeze.
This file encodes the hash of the model file, preventing tampering once frozen - forver locking a version of your algorithm code with your model file.
<!-- embedme examples/pytorch_image_classification/model_manifest.json.freeze -->
```json
{
   "required_files":[
      {
         "name":"squeezenet",
         "source_uri":"data://AlgorithmiaSE/image_cassification_demo/squeezenet1_1-f364aa15.pth",
         "fail_on_tamper":true,
         "metadata":{
            "dataset_md5_checksum":"46a44d32d2c5c07f7f66324bef4c7266"
         },
         "md5_checksum":"46a44d32d2c5c07f7f66324bef4c7266"
      },
      {
         "name":"labels",
         "source_uri":"data://AlgorithmiaSE/image_cassification_demo/imagenet_class_index.json",
         "fail_on_tamper":true,
         "metadata":{
            "dataset_md5_checksum":"46a44d32d2c5c07f7f66324bef4c7266"
         },
         "md5_checksum":"c2c37ea517e94d9795004a39431a14cb"
      }
   ],
   "optional_files":[
      {
         "name":"mobilenet",
         "source_uri":"data://AlgorithmiaSE/image_cassification_demo/mobilenet_v2-b0353104.pth",
         "fail_on_tamper":false,
         "metadata":{
            "dataset_md5_checksum":"46a44d32d2c5c07f7f66324bef4c7266"
         }
      }
   ],
   "timestamp":"1633450866.985464",
   "lock_checksum":"24f5eca888d87661ca6fc08042e40cb7"
}
```

As you can link to both hosted data collections, and AWS/GCP/Azure based block storage media, you're able to link your algorithm code with your model files, wherever they live today.


## Datarobot MLOps Integration
As part of the integration with Datarobot, we've built out integration support for the [DataRobot MLOps Agent](https://docs.datarobot.com/en/docs/mlops/deployment/mlops-agent/index.html)
By selecting `mlops=True` as part of the ADK `init()` function, the ADK will configure and setup the MLOps Agent to support writing content directly back to DataRobot.


For this, you'll need to select an MLOps Enabled Environment; and you will need to setup a DataRobot External Deployment.
Once setup, you will need to define your `mlops.json` file, including your deployment and model ids.

<!-- embedme examples/mlops_hello_world/mlops.json -->
```json
{
  "model_id": "YOUR_MODEL_ID",
  "deployment_id": "YOUR_DEPLOYMENT_ID",
  "datarobot_mlops_service_url": "https://app.datarobot.com"
}
```

Along with defining your `DATAROBOT_MLOPS_API_TOKEN` as a secret to your Algorithm, you're ready to start sending MLOps data back to DataRobot!

<!-- embedme examples/mlops_hello_world/src/Algorithm.py -->
```python
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


```



## Readme publishing
To compile the template readme, please check out [embedme](https://github.com/zakhenry/embedme) utility
and run the following:
```commandline
npm install -g npx
npx embedme --stdout README_template.md > README.md
```

## To publish a new version 
Publishing should be automatic on new releases, but if you wish to publish manually this is the process
first make sure to update the version in [setup.py](setup.py)
Then go through the following
Then, install these python dependencies
```commandline
pip install wheel==0.33
pip install setuptools==41.6
pip install twine==1.15
```

Setup your ~/.pypirc file:
```commandline
index-servers =
  pypi
  pypitest

[pypi]
repository: https://upload.pypi.org/legacy/
username: algorithmia
password: {{...}}

[pypitest]
repository: https://test.pypi.org/legacy/
username: algorithmia
password: {{...}}
```
The passwords (and the pypirc file itself) can be found in our devtools service
Make sure to update your setup.py with the new version before compiling.
Also make sure that this is created on Linux and not any other platform.
Compile via setup.py:
```commandline
python setup.py sdist bdist_wheel --universal
python -m twine upload -r pypitest dist/*

```
Verify that it works on pytest, then:
```commandline
python -m twine upload -r pypi dist/*
```
and you're done :)