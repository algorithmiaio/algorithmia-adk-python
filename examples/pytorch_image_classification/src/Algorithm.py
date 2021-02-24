import Algorithmia
from adk import ADK
import torch
from PIL import Image
import json
from torchvision import models, transforms

CLIENT = Algorithmia.client()
SMID_ALGO = "algo://util/SmartImageDownloader/0.2.x"
LABEL_PATH = "data://AlgorithmiaSE/image_cassification_demo/imagenet_class_index.json"
MODEL_PATHS = {
    "squeezenet": 'data://AlgorithmiaSE/image_cassification_demo/squeezenet1_1-f364aa15.pth',
    'alexnet': 'data://AlgorithmiaSE/image_cassification_demo/alexnet-owt-4df8aa71.pth',
}


def load_labels():
    local_path = CLIENT.file(LABEL_PATH).getFile().name
    with open(local_path) as f:
        labels = json.load(f)
    labels = [labels[str(k)][1] for k in range(len(labels))]
    return labels


def load_model(name):
    if name == "squeezenet":
        model = models.squeezenet1_1()
        models.densenet121()
        weights = torch.load(CLIENT.file(MODEL_PATHS['squeezenet']).getFile().name)
    else:
        model = models.alexnet()
        weights = torch.load(CLIENT.file(MODEL_PATHS['alexnet']).getFile().name)
    model.load_state_dict(weights)
    return model.float().eval()


def get_image(image_url):
    input = {"image": image_url, "resize": {'width': 224, 'height': 224}}
    result = CLIENT.algo(SMID_ALGO).pipe(input).result["savePath"][0]
    local_path = CLIENT.file(result).getFile().name
    img_data = Image.open(local_path)
    return img_data


def infer_image(image_url, n, state):
    model = state['model']
    labels = state['labels']
    image_data = get_image(image_url)
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


def load():
    output = {'model': load_model("squeezenet"), 'labels': load_labels()}
    return output


def apply(input, state):
    if isinstance(input, dict):
        if "n" in input:
            n = input['n']
        else:
            n = 3
        if "data" in input:
            if isinstance(input['data'], str):
                output = infer_image(input['data'], n, state)
            elif isinstance(input['data'], list):
                for row in input['data']:
                    row['predictions'] = infer_image(row['image_url'], n, state)
                output = input['data']
            else:
                raise Exception("'data' must be a image url or a list of image urls (with labels)")
            return output
        else:
            raise Exception("'data' must be defined")
    else:
        raise Exception('input must be a json object')


algo = ADK(apply_func=apply, load_func=load)
algo.serve({"data": "https://i.imgur.com/bXdORXl.jpeg"})
