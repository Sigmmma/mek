#!/usr/bin/python3
import io
import sys
import tatsu
from argparse import ArgumentParser

# Author: Conscars <inbox@t3hz0r.com>, 2020-03-05
VERSION_STR = "1.0.0"

# What follows is an EBNF grammar for the subset of VRML 1.0 which tool ouputs.
# It's used to generate a parser which can load the files into syntax tree for
# easier reformatting into OBJ. See the tatsu syntax docs for more info:
# https://tatsu.readthedocs.io/en/stable/syntax.html
WRL_PARSER = tatsu.compile("""
    @@grammar::VRML1
    # This just cleans up some information we don't need from the AST
    @@parseinfo::False

    # WRL files consist of a list of "Separator" nodes, one for each error found
    # by Tool. This grammar already treats whitespace as a token separator, so a
    # reformatted WRL file will still parse.
    start = '#VRML V1.0 ascii' { @+:separator }* $ ;

    # Each separator can the following properties, in this order:
    separator =
        'Separator'
        '{'
            # The coordinates array contains all vertices which are referenced
            # by index later.
            [ 'Coordinate3' '{' 'point' '[' coords:points ']' '}' ]

            # The material binding tells us how material properties are used.
            # correspond to the coordinates above, or faces.
            [ 'MaterialBinding' '{' 'value' mtl_binding:binding_type '}' ]

            # The material has two sub-sections whose lengths are not guaranteed
            # to match. The diffuseColor array contains a number of float
            # triplets (RGB) equal to the number of bound elements. However, in
            # the case of PER_FACE bound materials, the transparency array has
            # a single float rather than one per diffuseColor.
            [
                'Material'
                '{'
                    'diffuseColor' '[' mtl_diffuse_colors:points ']'
                    'transparency[' mtl_transparencies:floats ']'
                '}'
            ]

            # An indexed line set contains 1 or more edges, each defined by a
            # pair of indexes into the coords array.
            [
                'IndexedLineSet'
                '{'
                    'coordIndex' '[' indexed_lines:index_groups ']'
                '}'
            ]

            # Similarly to the indexed lines, the faces are triplets of indexes.
            [
                'IndexedFaceSet'
                '{'
                    'coordIndex' '[' indexed_faces:index_groups ']'
                '}'
            ]
        '}'
        ;

    # If the binding type is PER_VERTEX, then the material properties map to the
    # coordinates array. For PER_FACE, they map to the IndexedFaceSet.
    binding_type = 'PER_VERTEX' | 'PER_FACE' ;

    # Index arrays appear "flat", but actually use -1 as a terminator marking
    # the end of spans of indexes within. There's never actually any negative
    # indexes. Also note that the indexes may sometimes be output in a single
    # line, or when there's many values they can be output over multiple lines
    # in which case they will also gain a trailing comma before the closing "]".
    index_groups = { @+:index_group ',' } [ @+:index_group ] ;
    index_group = { @+:index ',' }+ '-1' ;
    index = /\\d+/ ;

    # Within an array, points are separated by comma (optional trailing comma)
    points = { @+:point ',' } [ @+:point ] ;
    # Points/colours are float triplets separated by whitespace.
    point = x:float y:float z:float ;

    # The only places where a comma-separated list of single floats is seen is
    # the transparency material property.
    floats = { @+:float ',' } [ @+:float ] ;

    # Floats can be negative and always have a 6 digit decimal part
    float = /-?\\d+\\.\\d+/ ;
""")

def parse_wrl_to_ast(wrl_content):
    '''
    Given a string of the WRL content, returns its abstract syntax tree.
    '''
    return WRL_PARSER.parse(wrl_content)

def convert_wrl_to_obj(input_stream, output_stream):
    '''
    Translates the WRL input stream to an OBJ output stream.
    The caller is responsible for closing streams.
    '''
    def output(line):
        print(line, file=output_stream)

    vert_index = 1 # Vertex indexes start at 1 in OBJ
    lines = []
    faces = []

    output("# This is a converted tool.exe WRL file. Import with settings Y forward and Z up")

    for separator in parse_wrl_to_ast(input_stream.read()):
        # For lines and faces, convert the separator-relative indexes into
        # global OBJ-relative ones, which we add to arrays to print later:
        if separator.indexed_faces:
            for indexed_face in separator.indexed_faces:
                faces.append([int(i) + vert_index for i in indexed_face])
        if separator.indexed_lines:
            for indexed_line in separator.indexed_lines:
                lines.append([int(i) + vert_index for i in indexed_line])
        for coord in separator.coords:
            # Put a list of all vertices at the start of the output
            output("v {x} {y} {z}".format(**coord))
            vert_index += 1

    # Finish up by outputting all the faces and lines. Note that all the
    # grouping information was lost in this process and we are ignoring some
    # data from the WRL. There's room for improvement here to infer error type
    # by colour, and name objects. Would be best as a Blender plugin.
    for face in faces:
        output("f {0} {1} {2}".format(*face))
    for line in lines:
        output("l {0} {1}".format(*line))

if __name__== "__main__":
    parser = ArgumentParser(description="Converts tool's .wrl files from VRML1.0 format to OBJ for importing to Blender. Version %s" % VERSION_STR)
    parser.add_argument('--version', action='version', version=VERSION_STR)
    parser.add_argument('--input', help='Path to an input .wrl file. If not passed, input is read from stdin.')
    parser.add_argument('--output', help='Output file path. If not passed, the OBJ file is written to stdout.')
    cmd_args = parser.parse_args()
    try:
        input_stream = io.open(cmd_args.input, "r", encoding="utf-8") if cmd_args.input else sys.stdin
        output_stream = io.open(cmd_args.output, "w", encoding="utf-8") if cmd_args.output else sys.stdout
        convert_wrl_to_obj(input_stream, output_stream)
    except Exception as e:
        print("Failed to convert WRL: %s" % e, file=sys.stderr)
        raise e
    finally:
        input_stream.close()
        output_stream.close()
