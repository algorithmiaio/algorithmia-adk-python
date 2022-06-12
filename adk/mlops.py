import yaml
import json
import os
import subprocess


class MLOps(object):
    spool_dir = "/tmp/ta"
    agent_dir = "/opt/mlops-agent/datarobot_mlops_package-8.1.2"

    def __init__(self, api_token, path):
        self.token = api_token
        if os.path.exists(path):
            with open(path) as f:
                mlops_config = json.load(f)
        else:
            raise Exception("'mlops.json' file does not exist, but mlops was requested.")
        if not os.path.exists(agent_dir):
            raise Exception("environment is not configured for mlops.\nPlease select a valid mlops enabled environment.")
        self.endpoint = mlops_config['datarobot_api_endpoint']
        self.model_id = mlops_config['model_id']
        self.deployment_id = mlops_config['deployment_id']

    def init(self):
        os.environ['MLOPS_DEPLOYMENT_ID'] = self.deployment_id
        os.environ['MLOPS_MODEL_ID'] = self.model_id
        os.environ['MLOPS_SPOOLER_TYPE'] = "FILESYSTEM"
        os.environ['MLOPS_FILESYSTEM_DIRECTORY'] = "/tmp/ta"

        with open(f'{self.agent_dir}/conf/mlops.agent.conf.yaml') as f:
            documents = yaml.load(f, Loader=yaml.FullLoader)
        documents['mlopsUrl'] = self.endpoint
        documents['apiToken'] = self.token
        with open(f'{self.agent_dir}/conf/mlops.agent.conf.yaml', 'w') as f:
            yaml.dump(documents, f)

        subprocess.call(f'{self.agent_dir}/bin/start-agent.sh')
        check = subprocess.Popen([f'{self.agent_dir}/bin/status-agent.sh'], stdout=subprocess.PIPE)
        output = check.stdout.readlines()[0]
        check.terminate()
        if b"DataRobot MLOps-Agent is running as a service." in output:
            return True
        else:
            raise Exception(output)