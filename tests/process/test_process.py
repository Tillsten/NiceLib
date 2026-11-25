from util import local_fpath
import pytest

from nicelib.process import CPPTypedefAdder, process_headers, process_source
from nicelib.parser.cpp_parser import CPPParser
from pycparser import c_ast
from pycparser.c_parser import ParseError as CParseError


def test_exclude_sys_funcdefs():
    header_src, _, _ = process_headers(local_fpath(__file__, 'general/sys-funcdef-a.h'))
    assert 'program_func' in header_src
    assert 'created_func' in header_src
    assert 'sys_func' not in header_src


def test_argnames():
    _, _, argnames = process_headers(local_fpath(__file__, 'general/argnames.h'))
    assert argnames['f'] is None
    assert argnames['f_void'] == []
    assert argnames['f_int'] == [None]
    assert argnames['f_int_int'] == [None, None]

    assert argnames['f_inta'] == ['a']
    assert argnames['f_inta_intb'] == ['a', 'b']

    assert argnames['f_ptra'] == ['a']
    assert argnames['f_arra'] == ['a']

    assert argnames['f_structa'] == ['a']
    assert argnames['f_structptra'] == ['a']


def test_cpp_parser_handles_references_and_typed_enums():
    tree = CPPParser().parse(
        'typedef int Count; int get(Count& count); '
        'enum Kind : unsigned int { KIND_VALUE = 1 };'
    )

    param_type = tree.ext[1].type.args.params[0].type
    assert isinstance(param_type, c_ast.PtrDecl)
    assert tree.ext[2].type.name == 'Kind'


def test_process_source_adds_context_to_pycparser_errors():
    with pytest.raises(CParseError, match='When parsing chunk'):
        process_source('int invalid(;')


def test_cpp_typedef_adder_builds_ast_with_current_pycparser():
    parser = CPPParser()
    tree = parser.parse_chunk('struct Foo { int value; };')

    tree = CPPTypedefAdder().hook(tree, parser.parse_chunk)

    assert isinstance(tree.ext[0].type, c_ast.Typedef)
    assert parser.parse_chunk('Foo bar;').ext[0].name == 'bar'


def test_cpp_parser_parse_resets_scope_and_coordinates():
    parser = CPPParser()
    parser.parse('\ntypedef int Count;', filename='first.h')

    tree = parser.parse('int value;', filename='second.h')

    assert str(tree.ext[0].coord).startswith('second.h:1')
    with pytest.raises(CParseError):
        parser.parse('Count value;', filename='third.h')
