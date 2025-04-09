import ply.lex as lex
import ply.yacc as yacc
import sys
import os

# --- Lexer ---

tokens = (
    'MODULE',
    'CASE',
    'AS',
    'ACTOR',
    'CONNECT',
    'EXTEND',
    'INCLUDE',
    'GENERALIZE',
    'SIMPLEDIR',
    'ID',
    'STRING',
    'LBRACE',
    'RBRACE',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'SEMICOLON',
)

t_LBRACE = r'{'
t_RBRACE = r'}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_SEMICOLON = r';'
t_CONNECT = r'--'
t_EXTEND = r'-e>'
t_INCLUDE = r'-i>'
t_GENERALIZE = r'->>'
t_SIMPLEDIR = r'->'
t_ignore = ' \t\n'

def t_MODULE(t):
    r'module'
    return t

def t_CASE(t):
    r'case'
    return t

def t_AS(t):
    r'as'
    return t

def t_ACTOR(t):
    r'actor'
    return t

def t_STRING(t):
    r'\"([^\\\"]|\\.)*\"|\'([^\\\']|\\.)*\''
    if t.value[0] == "'":
        t.value = '"' + t.value[1:-1] + '"'
    else:
        t.value = '"' + t.value[1:-1] + '"'
    return t

def t_ID(t):
    r'[a-zA-Z0-9_]+'
    return t

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at position {t.lexpos}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# --- Parser ---
modules = {}
actors = {}
connections = []

def p_program(p):
    '''program : statements'''
    p[0] = p[1]

def p_statements(p):
    '''statements : statement
                  | statements statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    '''statement : module_def
                 | actor_def
                 | connection'''
    p[0] = p[1]

def p_module_def(p):
    '''module_def : MODULE LPAREN STRING RPAREN LBRACE case_list RBRACE'''
    module_name = p[3]
    modules[module_name] = p[6]
    p[0] = ('module', module_name, p[6])

def p_case_list(p):
    '''case_list : case
                 | case_list COMMA case'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_case(p):
    '''case : CASE STRING AS ID
            | CASE STRING'''
            
    case_name = p[2]
    if len(p) == 5:
        case_id = p[4]
    else:
        case_id = None
         
    p[0] = ('case', case_name, case_id)

def p_actor_def(p):
    '''actor_def : ACTOR STRING AS ID SEMICOLON
                 | ACTOR STRING SEMICOLON'''
    actor_name = p[2]
    if len(p) == 6:
        actor_id = p[4]
    else:
        actor_id = None
    actors[actor_name] = actor_id
    p[0] = ('actor', actor_name, actor_id)

def p_connection(p):
    '''connection : ID CONNECT ID
                  | ID EXTEND ID
                  | ID INCLUDE ID
                  | ID GENERALIZE ID
                  | ID SIMPLEDIR ID
                  | ID CONNECT STRING
                  | ID EXTEND STRING
                  | ID INCLUDE STRING
                  | ID GENERALIZE STRING
                  | ID SIMPLEDIR STRING    
                  | STRING CONNECT ID
                  | STRING EXTEND ID
                  | STRING INCLUDE ID
                  | STRING GENERALIZE ID
                  | STRING SIMPLEDIR ID
                  | STRING CONNECT STRING
                  | STRING EXTEND STRING
                  | STRING INCLUDE STRING
                  | STRING GENERALIZE STRING
                  | STRING SIMPLEDIR STRING'''
                   
    source = p[1]
    connection_type = p[2]
    target = p[3]
    
    if connection_type == '--':
        plantuml_conn = ['--']
    elif connection_type == '-e>':
        plantuml_conn = ['..>', '<<extend>>']
    elif connection_type == '-i>':
        plantuml_conn = ['..>', '<<include>>']
    elif connection_type == '->>':
        plantuml_conn = ['..|>']
    elif connection_type == '->':
        plantuml_conn = ['-->']
    
    connections.append((source, plantuml_conn, target))
    p[0] = ('connection', source, connection_type, target)

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}', position {p.lexpos}")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc(debug=True, errorlog=yacc.NullLogger())  # Reduce verbose output

# Function to convert the parsed data to PlantUML
def generate_plantuml(modules, actors, connections):
    output = "@startuml\nleft to right direction\n"
    
    for actor_name, actor_id in actors.items():
        if actor_id is None:
            output += f"actor {actor_name}\n"
        else:
            output += f"actor {actor_name} as {actor_id}\n"
    
    output += "\n"
    
    for module_name, cases in modules.items():
        output += f"package {module_name} {{\n"
        for case in cases:
            case_name = case[1]
            case_id = case[2]
            if case_id is None:
                output += f"    usecase {case_name}\n"
            else:
                output += f"    usecase {case_name} as {case_id}\n"
        output += "}\n\n"
    
    for source, conn_type, target in connections:        
        if len(conn_type) == 2:
            output += f"{source} {conn_type[0]} {target} : {conn_type[1]}\n"
        else:
            output += f"{source} {conn_type[0]} {target}\n"
    
    output += "@enduml"
    return output

def read_input_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def parse_and_generate(input_text):
    # Reset global variables
    global modules, actors, connections
    modules = {}
    actors = {}
    connections = []
    
    parser.parse(input_text, lexer=lexer)

    return generate_plantuml(modules, actors, connections)

# Process a file and generate output
def process_file(input_file, output_file=None):
    input_text = read_input_file(input_file)
    if input_text is None:
        return False
    
    plantuml_code = parse_and_generate(input_text)
    
    if output_file is None:
        file_name, _ = os.path.splitext(input_file)
        output_file = f"{file_name}.puml"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(plantuml_code)
        print(f"Successfully generated PlantUML code in '{output_file}'")
        return True
    except Exception as e:
        print(f"Error writing to output file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python uml_parser.py input_file [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    if process_file(input_file, output_file):
        sys.exit(0)
    else:
        sys.exit(1)