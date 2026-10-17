"""explainer-compose.py imported as a module (its file name has a hyphen), for unit tests of its helpers."""
import importlib.util, os

_spec = importlib.util.spec_from_file_location("explainer_compose", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "explainer-compose.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
