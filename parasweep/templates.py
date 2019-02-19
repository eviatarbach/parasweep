"""Template engines for generating configuration files."""
from abc import ABC, abstractmethod
from string import Formatter


class Template(ABC):
    """
    Abstract base class for template engines.

    Subclasses should implement the ``load`` and ``render`` methods. Make sure
    to implement errors for providing parameters not present in the template,
    and for using parameters in the template that are not provided.

    """

    @abstractmethod
    def load(self, paths):
        """
        Load configuration templates.

        Parameters
        ----------
        paths : list
            List of paths of configuration templates to load.

        """
        pass

    @abstractmethod
    def render(self, params):
        """
        Render a configuration file with the template engine.

        Parameters
        ----------
        params : dict
            Dictionary with parameters and their values.

        """
        pass


class PythonFormatTemplate(Template):
    """Template engine using Python's string formatting."""

    def load(self, paths):
        self.templates = []
        for path in paths:
            with open(path, 'r') as template_file:
                self.templates.append(template_file.read())

    def render(self, params):
        keys = params.keys()
        unused_names = set(keys)
        rendered = []
        for template in self.templates:
            config_names = set([elem[1] for elem in
                                Formatter().parse(template) if elem[1]])
            unused_names -= config_names
            try:
                rendered.append(template.format(**params))
            except KeyError as key:
                raise NameError(f'The name {key} is used in the template but '
                                'not provided.')
        if unused_names:
            raise NameError(f'The names {unused_names} are not used in the '
                            'template.')
        return rendered


def _mako_template_names(template):
    """
    Return all the used identifiers in the Mako template.

    From Igonato's code at https://stackoverflow.com/a/23577289/622408.
    """
    from mako import lexer, codegen

    lexer = lexer.Lexer(template)
    node = lexer.parse()
    # ^ The node is the root element for the parse tree.
    # The tree contains all the data from a template
    # needed for the code generation process

    # Dummy compiler. _Identifiers class requires one
    # but only interested in the reserved_names field
    compiler = lambda: None
    compiler.reserved_names = set()

    identifiers = codegen._Identifiers(compiler, node)
    return identifiers.undeclared


class MakoTemplate(Template):
    """Template engine using Mako."""

    def load(self, paths):
        from mako.template import Template

        self.templates = []
        for path in paths:
            self.templates.append(Template(filename=path,
                                           input_encoding='utf-8',
                                           strict_undefined=True))

    def render(self, params):
        keys = params.keys()
        unused_names = set(keys)
        rendered = []
        for template in self.templates:
            config_names = _mako_template_names(template.source)
            unused_names -= config_names
            rendered.append(template.render_unicode(**params))
        if unused_names:
            raise NameError(f'The names {unused_names} are not used in the '
                            'template.')
        return rendered
