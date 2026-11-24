# -*- coding: utf-8 -*-
# Copyright 2018 Nate Bogdanowicz

# Modeled after pycparserext
from __future__ import division

from pycparser.c_parser import CParser
from pycparser import c_ast

from .cpp_lexer import CPPLexer


class CPPParser(CParser):
    def __init__(self, **kwds):
        kwds['lexer'] = CPPLexer
        kwds['lextab'] = 'nicelib.parser.lextab'
        kwds['yacctab'] = 'nicelib.parser.yacctab'
        CParser.__init__(self, **kwds)
        self._uses_recursive_parser = not hasattr(self, 'cparser')
        if self._uses_recursive_parser:
            self.clex.cpp_parser = self

    def parse(self, text, filename='', debug=False):
        self.clex.reset_cpp_state()
        return CParser.parse(self, text, filename, debug)

    def parse_chunk(self, text, reset_file=False):
        """Parse one chunk while retaining the translation unit's scope."""
        if not self._uses_recursive_parser:
            if reset_file:
                self.clex.filename = '<generator>'
                self.clex.reset_lineno()
            self._last_yielded_token = None
            return self.cparser.parse(input=text, lexer=self.clex, debug=0)

        if reset_file:
            filename = '<generator>'
        else:
            filename = self.clex.filename

        self.clex.reset_cpp_state()
        self.clex.input(text, filename)
        self._tokens = type(self._tokens)(self.clex.token)
        self._typedef_checked_token = None

        tree = self._parse_translation_unit_or_empty()
        token = self._peek()
        if token is not None:
            self._parse_error('before: {}'.format(token.value), self._tok_coord(token))
        return tree

    # Parse pass-by-ref args as pointers
    def p_pointer(self, p):
        """ pointer : TIMES type_qualifier_list_opt
                    | TIMES type_qualifier_list_opt pointer
                    | AND type_qualifier_list_opt
                    | AND type_qualifier_list_opt pointer
        """
        return CParser.p_pointer(self, p)

    # Parse typed enums, but ignore the types
    def p_enum_specifier_4(self, p):
        """ enum_specifier : ENUM ID COLON declaration_specifiers brace_open enumerator_list brace_close
                           | ENUM TYPEID COLON declaration_specifiers brace_open enumerator_list brace_close
        """
        p[0] = c_ast.Enum(p[2], p[6], self._token_coord(p, 1))
