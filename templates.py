from abc import ABC, abstractmethod


class _Template(ABC):
    def __init__(self, text=None, path=None):
        if (((path is None) and (text is None))
                or (not (path is None) and not (text is None))):
            raise ValueError('Exactly one of `path` or `text` must be provided.')
        self.text = text
        self.path = path
        self._load()

    @abstractmethod
    def _load(self):
        pass

    @abstractmethod
    def render(self, params):
        pass


def _mako_template_names(template):
    """
    Return all the used identifiers in the template.

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


class MakoTemplate(_Template):
    def _load(self):
        from mako.template import Template

        if self.path:
            self.template = Template(filename=self.path, input_encoding='utf-8',
                                     strict_undefined=True)
        else:
            self.template = Template(text=self.text, input_encoding='utf-8',
                                     strict_undefined=True)

    def render(self, params):
        keys = params.keys()
        config_names = _mako_template_names(self.template.source)
        unused_names = set(keys) - config_names
        if unused_names:
            raise NameError('The names {unused_names} are not used in the template.'.format(unused_names=unused_names))
        return self.template.render_unicode(**params).encode('utf-8', 'replace')
