import json
import os
import urllib

import requests
import time
import base64

APIHOST='http://172.17.0.1:3233/api/v1'

headers = {'Authorization': 'Basic MjNiYzQ2YjEtNzFmNi00ZWQ1LThjNTQtODE2YWE0ZjhjNTAyOjEyM3pPM3haQ0xyTU42djJCS0sxZFhZRnBYbFBrY2NPRnFtMTJDZEFzTWdSVTRWck5aOWx5R1ZDR3VNREdJd1A='}

def sync_call(action_name: str, params: dict):
    url = APIHOST+'/namespaces/_/actions/'+action_name+'?blocking=true&result=true&workers=1'
    start_time = time.time()
    response = requests.post(url, json=params, headers=headers, timeout=600)
    elapsed_time = time.time() - start_time
    print('REQUEST:', response.request.__dict__)
    return response.text, elapsed_time


def async_call(action_name: str, params: dict):
    url = APIHOST+'/namespaces/_/actions/'+action_name+'?blocking=false&result=true&workers=1'

    response = requests.post(url, json=params, headers=headers, timeout=600)
    print('REQUEST:', response.request.__dict__)
    data = json.loads(response.text)
    activation_id = data["activationId"]
    return activation_id


def get_results(activation_id):
    url = APIHOST + '/namespaces/_/activations/' + activation_id

    # Wait until the worker completes the job
    while True:
        result = requests.get(url, headers=headers, timeout=600)
        if result.status_code == 200:
            break
        time.sleep(0.001)

    result = json.loads(result.text)
    print('duration:', result['duration'], 'ms')
    return result['response']['result']



# Get the image paths from imagenet/ directory
def list_image_paths(directory_path, num_images):
    urls_general = [directory_path + f for f in os.listdir(directory_path) if
                    os.path.isfile(os.path.join(directory_path, f))]
    urls_general = urls_general[:num_images]
    return urls_general

# Execute experiment
def model_parts(model_links):
    start_time = time.time()
    req_body = {
        'models': model_links,
        'replace_images': '',
    }

    activation_id = async_call('model_parts', req_body)
    response = get_results(activation_id)
    try:
        response = response['result']
    except:
        pass

    elapsed_time = time.time() - start_time
    return response, elapsed_time



def create_experiments (model_name, min_parts, max_parts):
    # model_experiments = [
    #     ['https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/1/0.pt'],
    #     ['https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/2/0.pt', 'https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/2/1.pt'],
    #     ['https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/3/0.pt', 'https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/3/1.pt', 'https://huggingface.co/pepecalero/TorchscriptSplitModels/resolve/main/resnet_152/3/2.pt']
    # ]
    model_experiments = []
    for i in range(min_parts, max_parts+1):
        model_parts = []
        for j in range(i):
            model_parts.append(f'https://huggingface.co/pepecalero/TorchscriptSplitModelsOriginal/resolve/main/{model_name}/{i}/{j}.pt')
        model_experiments.append(model_parts)
    return model_experiments

def main():
    model_name = 'resnet_152' # 'squeezenet1_1' or 'resnet_152' or 'resnet50' or 'resnet_18' or 'mobilenet_v3_large'
    min_parts = 1
    max_parts = 20 # 8 or 20 or 11 or 5 or 11
    model_experiments = create_experiments(model_name, min_parts, max_parts)
    results = []
    for model_experiment in model_experiments:
        model_parts(model_experiment)
        responses, elapsed_time = model_parts(model_experiment)
        print('\nRESPONSES:', json.dumps(responses, indent=4))
        print('TIME TAKEN:', elapsed_time)
        results.append({'responses': responses, 'elapsed_time': elapsed_time})

    # Save in json
    with open('model_parts.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':
    main()