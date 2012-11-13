version = '1.0'
import os
dirlist = os.listdir(os.path.dirname(__file__))
__all__ = [x[:-3] for x in dirlist if x.endswith('.py') and x != '__init__.py']
