import yaml
import json
import os
import subprocess


class MLOps(object):
    spool_dir = "/tmp/ta"
    agent_dir = "/opt/mlops-agent"
    mlops_dir_name = "datarobot_mlops_package-8.1.2"

    def __init__(self, api_token, path):
        self.token = api_token
        if os.path.exists(path):
            with open(path) as f:
                mlops_config = json.load(f)
        else:
            raise Exception("'mlops.json' file does not exist, but mlops was requested.")
        if not os.path.exists(self.agent_dir):
            raise Exception("environment is not configured for mlops.\nPlease select a valid mlops enabled environment.")
        self.endpoint = mlops_config['datarobot_mlops_service_url']
        self.model_id = mlops_config['model_id']
        self.deployment_id = mlops_config['deployment_id']
        self.mlops_name = mlops_config.get('mlops_dir_name', 'datarobot_mlops_package-8.1.2')

    def init(self):
        os.environ['MLOPS_DEPLOYMENT_ID'] = self.deployment_id
        os.environ['MLOPS_MODEL_ID'] = self.model_id
        os.environ['MLOPS_SPOOLER_TYPE'] = "FILESYSTEM"
        os.environ['MLOPS_FILESYSTEM_DIRECTORY'] = self.spool_dir

        with open(f'{self.agent_dir}/{self.mlops_dir_name}/conf/mlops.agent.conf.yaml') as f:
            documents = yaml.load(f, Loader=yaml.FullLoader)
        documents['mlopsUrl'] = self.endpoint
        documents['apiToken'] = self.token
        with open(f'{self.agent_dir}/{self.mlops_dir_name}/conf/mlops.agent.conf.yaml', 'w') as f:
            yaml.dump(documents, f)

        subprocess.call(f'{self.agent_dir}/{self.mlops_dir_name}/bin/start-agent.sh')
        check = subprocess.Popen([f'{self.agent_dir}/{self.mlops_dir_name}/bin/status-agent.sh'], stdout=subprocess.PIPE)
        output = check.stdout.readlines()[0]
        check.terminate()
        if b"DataRobot MLOps-Agent is running as a service." in output:
            return True
        else:
            raise Exception(output)