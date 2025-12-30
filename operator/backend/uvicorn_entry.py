import os
import importlib.util
import uvicorn

here = os.path.dirname(__file__)
mod_path = os.path.join(here, "main.py")

spec = importlib.util.spec_from_file_location("vx11_operator_main", mod_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = getattr(module, "app")

if __name__ == "__main__":
    port = int(os.environ.get("OPERATOR_PORT", "8011"))
    uvicorn.run(app, host="0.0.0.0", port=port)
