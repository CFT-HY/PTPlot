"""Django admin site configuration."""

from . import auth, base, model, parameter_choice, scenario
from .auth import *
from .base import *
from .model import *
from .parameter_choice import *
from .scenario import *

__all__: list[str] = []
__all__ += auth.__all__
__all__ += base.__all__
__all__ += model.__all__
__all__ += parameter_choice.__all__
__all__ += scenario.__all__
