"""Data models"""

# Re-export models from the parent models.py file
# This package (app/models/) re-exports everything from app/models.py
# to allow imports like: from app.models import Message

import importlib.util
from pathlib import Path

# Load the parent models.py file directly
parent_dir = Path(__file__).parent.parent
models_file = parent_dir / "models.py"

# Create a module spec and load it
spec = importlib.util.spec_from_file_location("app.models_file", models_file)
_models_module = importlib.util.module_from_spec(spec)

# Execute the module (this will run models.py and create all the classes)
spec.loader.exec_module(_models_module)

# Re-export all models
AccessLevel = _models_module.AccessLevel
RiskLevel = _models_module.RiskLevel
User = _models_module.User
ProtectedUser = _models_module.ProtectedUser
Guardian = _models_module.Guardian
Message = _models_module.Message
SharedMessage = _models_module.SharedMessage
GuardianInvitation = _models_module.GuardianInvitation

__all__ = [
    "AccessLevel",
    "RiskLevel",
    "User",
    "ProtectedUser",
    "Guardian",
    "Message",
    "SharedMessage",
    "GuardianInvitation",
]

