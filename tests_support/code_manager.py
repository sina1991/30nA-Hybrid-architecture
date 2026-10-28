import io
import zipfile


def make_zip():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("main.py", "def run(value):\n    return value\n")
    return stream.getvalue()


class FakeDataManager:
    def __init__(self):
        self.models = {}
        self.resources = {}
        self.records = {}
        self.next_record_id = 1

    def register_model(self, model):
        from code_manager.data_manager_client import DataManagerAPIError

        key = (model["model_id"], model["version"])
        existing = self.models.get(key)
        if existing is not None and existing != model:
            raise DataManagerAPIError(
                status=409,
                code="CONFLICT",
                message="model version already exists with a different definition",
                retryable=False,
                context={},
            )
        self.models[key] = model
        return model

    def create_resource(self, resource):
        resource_id = resource["resource_id"]
        model_id = resource["model_id"]
        model_version = resource["model_version"]
        if resource_id in self.resources:
            from code_manager.data_manager_client import DataManagerAPIError
            raise DataManagerAPIError(
                status=409,
                code="CONFLICT",
                message="already exists",
                retryable=False,
                context={},
            )
        self.resources[resource_id] = {
            "resource_id": resource_id,
            "model_id": model_id,
            "model_version": model_version,
        }
        self.records[resource_id] = []
        return self.resources[resource_id]

    def get_resource(self, resource_id):
        return self.resources[resource_id]

    def list_records(self, resource_id):
        return {"records": self.records[resource_id]}

    def write_record(self, resource_id, data):
        record = {
            "record_id": str(self.next_record_id),
            "resource_id": resource_id,
            "data": data,
        }
        self.next_record_id += 1
        self.records[resource_id].append(record)
        return record
