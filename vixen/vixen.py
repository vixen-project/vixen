
from traits.api import HasTraits, List

from .project import Project


class Vixen(HasTraits):

    projects = List(Project)
