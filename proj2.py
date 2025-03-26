import ply.lex as lex
import ply.yacc as yacc

# --- Lexer ---
tokens = (
    'MODULE',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'CASE',
    'APOSTROPHE',
    'AS',
    'COMMA',
    'SEMICOLON',
    'ACTOR',
    'ARROW',
    'DOUBLE_ARROW',
    'DASH_ARROW',
    'ARROW_DASH',
    'DASH_DASH',
    'STRING',
    'IDENTIFIER',
)

t_MODULE = r'module'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_CASE = r'case'
t_AS = r'as'
t_COMMA = r','
t_SEMICOLON = r';'
t_ACTOR = r'actor'
t_ARROW = r'->'
t_DOUBLE_ARROW = r'->>'
t_DASH_ARROW = r'--' + r'>'
t_ARROW_DASH = r'<' + r'--'
t_DASH_DASH = r'--'
t_APOSTROPHE = r"'"

def t_STRING(t):
    r"'.*?'|“.*?”"  # Aceita aspas simples e duplas (considerando a variação ')
    t.value = t.value[1:-1].strip()
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.value = t.value.strip()
    return t

t_ignore = ' \t\n'

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# --- Parser ---
precedence = ()

def p_program(p):
    '''program : definitions'''
    p[0] = p[1]

def p_definitions_empty(p):
    '''definitions :'''
    p[0] = {'actors': {}, 'modules': {}, 'relations': []}

def p_definitions_definition(p):
    '''definitions : definitions definition'''
    p[0] = p[1]
    if 'type' in p[2]:
        if p[2]['type'] == 'module':
            p[0]['modules'][p[2]['name']] = p[2]['cases']
        elif p[2]['type'] == 'actor':
            p[0]['actors'][p[2]['alias']] = p[2]['name']
        elif p[2]['type'] == 'relation':
            p[0]['relations'].append(p[2]['relation'])

def p_definition_module(p):
    '''definition : MODULE LPAREN IDENTIFIER RPAREN LBRACE cases RBRACE'''
    p[0] = {'type': 'module', 'name': p[3], 'cases': p[6]}

def p_cases_empty(p):
    '''cases :'''
    p[0] = []

def p_cases_case(p):
    '''cases : cases case_statement'''
    p[0] = p[1]
    p[0].append(p[2])

def p_case_statement(p):
    '''case_statement : CASE STRING AS IDENTIFIER COMMA'''
    p[0] = {'name': p[2], 'alias': p[4]}

def p_case_statement_last(p):
    '''case_statement : CASE STRING AS IDENTIFIER SEMICOLON'''
    p[0] = {'name': p[2], 'alias': p[4]}

def p_definition_actor(p):
    '''definition : ACTOR STRING AS IDENTIFIER SEMICOLON'''
    p[0] = {'type': 'actor', 'name': p[2], 'alias': p[4]}

def p_definition_relation(p):
    '''definition : IDENTIFIER ARROW IDENTIFIER SEMICOLON
                  | IDENTIFIER DOUBLE_ARROW IDENTIFIER SEMICOLON
                  | IDENTIFIER DASH_ARROW IDENTIFIER SEMICOLON
                  | IDENTIFIER ARROW_DASH IDENTIFIER SEMICOLON
                  | IDENTIFIER DASH_DASH IDENTIFIER SEMICOLON'''
    p[0] = {'type': 'relation', 'relation': f"{p[1]} {p[2]} {p[3]}"}

def p_error(p):
    if p:
        print(f"Syntax error at token '{p.type}' ({p.value})")
        # Discard the bad token and try to continue parsing
        parser.errok()
    else:
        print("Syntax error at EOF")

parser = yacc.yacc()

def generate_plantuml(parse_result):
    plantuml_output = "@startuml\n"

    # Adicionar atores
    for alias, nome in parse_result['actors'].items():
        plantuml_output += f"actor {alias} as \"{nome}\"\n"
    plantuml_output += "\n"

    # Adicionar pacotes e casos de uso
    for modulo_nome, casos in parse_result['modules'].items():
        plantuml_output += f"package \"{modulo_nome}\" {{\n"
        for caso in casos:
            plantuml_output += f"  usecase \"{caso['name']}\" as {caso['alias']}\n"
        plantuml_output += "}\n\n"

    # Adicionar relações
    for relacao in parse_result['relations']:
        plantuml_output += f"{relacao}\n"

    plantuml_output += "@enduml"
    return plantuml_output

def converter_com_ply(entrada):
    try:
        resultado_parse = parser.parse(entrada)
        if resultado_parse:
            return generate_plantuml(resultado_parse)
        else:
            return "Erro ao analisar a entrada."
    except Exception as e:
        return f"Erro durante a conversão: {e}"

# Seu texto de entrada (mantido)
entrada = """module(Sistema de Controle Predial) {
	case 'Alterar Empresa' as AE,
	case 'Consultar Empresa' as CoE,
	case 'Efetuar Login' as EL,
	case 'Cadastrar Empresa' as CaE,
	case 'Excluir Empresa' as EE,
	case '<<CRUD>> Manter Usuário' as CMU,
	case 'Enviar Acessos' as EA,
	case 'Enviar Temperaturas' as ET,
}

module(Sistema de Catraca){
	case 'Acessar Catraca' as AC,
	case 'Consultar Acessos' as CA,
}

module(Sistema de ArCondicionado){
	case 'Medir Temperatura' as MT,
}

actor 'Funcionário' as F;
actor 'Atendente' as A;
actor 'Síndico' as S;
actor 'Sistema de Catraca' as SC;
actor 'Sistema de Ar Condicionado' as SAC;
actor 'Sistema de Controle Predial' as SCP;

EA -> SC
ET -> SAC
MT -> SCP

S ->> A
A ->>F

F -- AE
F -- CoE
F -- EL
F -- AC
A -- CaE
A -- EE
A -- CMU
A -- EA
S -- CA
S -- ET
"""

plantuml_gerado_ply = converter_com_ply(entrada)
print(plantuml_gerado_ply)