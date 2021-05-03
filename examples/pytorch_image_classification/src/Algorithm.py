from Algorithmia import ADK
import Algorithmia
import torch
from PIL import Image
import json
from torchvision import models, transforms

def load_labels(label_path, client):
    local_path = client.file(label_path).getFile().name
    with open(local_path) as f:
        labels = json.load(f)
    labels = [labels[str(k)][1] for k in range(len(labels))]
    return labels


def load_model(model_paths, client):
    model = models.squeezenet1_1()
    local_file = client.file(model_paths["filepath"]).getFile().name
    weights = torch.load(local_file)
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

    globals = {}
    client = Algorithmia.client()
    globals["SMID_ALGO"] = "algo://util/SmartImageDownloader/0.2.x"
    globals["model"] = load_model(manifest["squeezenet"], client)
    globals["labels"] = load_labels(manifest["label_file"], client)
    return globals


def apply(input, globals):
    if isinstance(input, dict):
        if "n" in input:
            n = input["n"]
        else:
            n = 3
        if "data" in input:
            if isinstance(input["data"], str):
                output = infer_image(input["data"], n, globals)
            elif isinstance(input["data"], list):
                for row in input["data"]:
                    row["predictions"] = infer_image(row["image_url"], n, globals)
                output = input["data"]
            else:
                raise Exception("\"data\" must be a image url or a list of image urls (with labels)")
            return output
        else:
            raise Exception("\"data\" must be defined")
    else:
        raise Exception("input must be a json object")


algorithm = ADK(apply_func=apply, load_func=load)
algorithm.init({"data": "https://i.imgur.com/bXdORXl.jpeg"})
