# -*- coding: utf-8 -*-
# Copyright 2018 Nate Bogdanowicz

# Modeled after pycparserext
from pycparser.c_lexer import CLexer


class CPPLexer(CLexer):
    _type_qualifiers = frozenset(('const', 'volatile', 'restrict', '_Atomic'))
    _type_keywords = frozenset((
        'void', 'char', 'short', 'int', 'long', 'float', 'double', 'signed',
        'unsigned', '_Bool', 'bool',
    ))

    def reset_cpp_state(self):
        self._previous_tokens = []
        self._in_enum_header = False

    def token(self):
        token = super().token()
        if token is None:
            return None

        parser = getattr(self, 'cpp_parser', None)
        if parser is None:
            return token

        if token.type == 'ENUM':
            self._in_enum_header = True
        elif self._in_enum_header and token.value == ':':
            while token is not None and token.value not in ('{', ';'):
                token = super().token()
            self._in_enum_header = False
            if token is None:
                return None
        elif self._in_enum_header and token.value == ';':
            self._in_enum_header = False

        if token.value == '&' and self._is_reference(parser):
            token.type = 'TIMES'
            token.value = '*'

        self._previous_tokens.append(token)
        if len(self._previous_tokens) > 4:
            del self._previous_tokens[0]
        return token

    def _is_reference(self, parser):
        tokens = list(reversed(self._previous_tokens))
        while tokens and tokens[0].value in self._type_qualifiers:
            tokens.pop(0)

        if tokens and tokens[0].value == '*':
            tokens.pop(0)
            while tokens and tokens[0].value in self._type_qualifiers:
                tokens.pop(0)

        if not tokens:
            return False

        previous = tokens[0]
        if previous.value in self._type_keywords or parser._is_type_in_scope(previous.value):
            return True
        return len(tokens) > 1 and tokens[1].value in ('struct', 'union', 'enum')
