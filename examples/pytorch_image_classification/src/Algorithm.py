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


def load(manifest):

    state = {}
    state["SMID_ALGO"] = "algo://util/SmartImageDownloader/0.2.x"
    state["model"] = load_model(manifest.get_model("model_squeezenet"))
    state["labels"] = load_labels(manifest.get_model("labels"))
    return state


def apply(input, state):
    if isinstance(input, dict):
        if "n" in input:
            n = input["n"]
        else:
            n = 3
        if "data" in input:
            if isinstance(input["data"], str):
                output = infer_image(input["data"], n, state)
            elif isinstance(input["data"], list):
                for row in input["data"]:
                    row["predictions"] = infer_image(row["image_url"], n, state)
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
