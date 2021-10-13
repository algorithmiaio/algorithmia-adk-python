from adk import ADK


class ADKTest(ADK):
    def __init__(self, apply_func, load_func=None, client=None, manifest_path="model_manifest.json.freeze"):
        super(ADKTest, self).__init__(apply_func, load_func, client)
        self.model_data = self.init_manifest(manifest_path)
