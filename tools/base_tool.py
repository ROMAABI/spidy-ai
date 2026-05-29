class BaseTool:
    name        : str = ""
    description : str = ""

    def run(self, **kwargs):
        raise NotImplementedError