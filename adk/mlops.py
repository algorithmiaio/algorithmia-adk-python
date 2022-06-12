import yaml
import os
import subprocess


class MLOps(Object):
    def __init__(self, endpoint, api_token, model_id, deployment_id):
        self.token = api_token
        self.endpoint = endpoint
        self.model_id = model_id
        self.deployment_id = deployment_id
        self.spool_dir = "/tmp/ta"
        self.agent_dir = "/opt/mlops-agent/datarobot_mlops_package-8.1.2"

    def init(self):
        with open(f'{self.agent_dir}/conf/mlops.agent.conf.yaml') as f:
            documents = yaml.load(f, Loader=yaml.FullLoader)
        documents['mlopsUrl'] = self.endpoint
        documents['apiToken'] = self.token
        with open(f'{agents_dir}/conf/mlops.agent.conf.yaml', 'w') as f:
            yaml.dump(documents, f)

        subprocess.call(f'{agents_dir}/bin/start-agent.sh')
        check = subprocess.Popen([f'{agents_dir}/bin/status-agent.sh'], stdout=subprocess.PIPE)
        output = check.stdout.readlines()
        check.terminate()
        if "DataRobot MLOps-Agent is running as a service." in output:
            return True
        else:
            return False

    def env_vars(self):
        os.environ['MLOPS_DEPLOYMENT_ID'] = self.deployment_id
        os.environ['MLOPS_MODEL_ID'] = self.model_id
        os.environ['MLOPS_SPOOLER_TYPE'] = "FILESYSTEM"
        os.environ['MLOPS_FILESYSTEM_DIRECTORY'] = "/tmp/ta"