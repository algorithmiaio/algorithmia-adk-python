import yaml
import json
import os
import subprocess


class MLOps(object):
    spool_dir = "/tmp/ta"
    agent_dir = "/opt/mlops-agent"
    mlops_dir_name = "datarobot_mlops_package-8.1.2"
    total_dir_path = agent_dir + "/" + mlops_dir_name

    def __init__(self, api_token, path):
        self.token = api_token
        if os.path.exists(path):
            with open(path) as f:
                mlops_config = json.load(f)
            self.endpoint = mlops_config['datarobot_mlops_service_url']
            self.model_id = mlops_config['model_id']
            self.deployment_id = mlops_config['deployment_id']
            self.mlops_name = mlops_config.get('mlops_dir_name', 'datarobot_mlops_package-8.1.2')
        if "MLOPS_SERVICE_URL" in os.environ:
            self.endpoint = os.environ['MLOPS_SERVICE_URL']
        if "MODEL_ID" in os.environ:
            self.model_id = os.environ['MODEL_ID']
        if "DEPLOYMENT_ID" in os.environ:
            self.deployment_id = os.environ['DEPLOYMENT_ID']
        if not os.path.exists(self.agent_dir):
            raise Exception("environment is not configured for mlops.\nPlease select a valid mlops enabled environment.")

        if self.endpoint is None:
            raise Exception("'no endpoint found, please add 'MLOPS_SERVICE_URL' environment variable, or create an "
                            "mlops.json file")
        if self.model_id is None:
            raise Exception("no model_id found, please add 'MODEL_ID' environment variable, or create an mlops.json "
                            "file")
        if self.deployment_id is None:
            raise Exception("no deployment_id found, please add 'DEPLOYMENT_ID' environment variable, or create an "
                            "mlops.json file")

    def init(self):
        os.environ['MLOPS_DEPLOYMENT_ID'] = self.deployment_id
        os.environ['MLOPS_MODEL_ID'] = self.model_id
        os.environ['MLOPS_SPOOLER_TYPE'] = "FILESYSTEM"
        os.environ['MLOPS_FILESYSTEM_DIRECTORY'] = self.spool_dir

        with open(self.total_dir_path + '/conf/mlops.agent.conf.yaml') as f:
            documents = yaml.load(f, Loader=yaml.FullLoader)
        documents['mlopsUrl'] = self.endpoint
        documents['apiToken'] = self.token
        with open(self.total_dir_path + '/conf/mlops.agent.conf.yaml', 'w') as f:
            yaml.dump(documents, f)

        subprocess.call(self.total_dir_path + '/bin/start-agent.sh')
        check = subprocess.Popen([self.total_dir_path + '/bin/status-agent.sh'], stdout=subprocess.PIPE)
        output = check.stdout.readlines()[0]
        check.terminate()
        if b"DataRobot MLOps-Agent is running as a service." in output:
            return True
        else:
            raise Exception(output)
