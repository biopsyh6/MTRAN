import re
from typing import List, Tuple, Optional
from tokenModel import Token, TokenType
from difflib import get_close_matches

class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.token_list: List[Token] = [] # Список всех найденных токенов
        self.names_token_list: List[Token] = [] # Список токенов, которые являются переменными или константами
        self.keywords_token_list: List[Token] = [] # Список токенов, которые являются ключевыми словами
        self.operators_token_list: List[Token] = [] # Список токенов, которые являются операторами
        self.punctuations_token_list: List[Token] = [] # Список токенов, которые являются знаками пунктуации

        self.names_index = 0
        self.table_names = {}
        self.operators_index = 0
        self.table_operators = {}
        self.punctuations_index = 0
        self.table_punctuations = {}
        self.keywords_index = 0
        self.table_keywords = {}

        self.bracket_stack = []

    def lex_analyze(self) -> List[Token]:
        errors = []
        while True:
            res, err = self.next_token()
            if not res:
                break
            if err:
                errors.append(err)

        # Проверка незакрытых скобок
        while self.bracket_stack:
            bracket, line, col = self.bracket_stack.pop()
            errors.append(f"Ошибка: незакрытая скобка '{bracket}' на позиции {line}:{col}")
        
        for error in errors:
            print(error)

        return self.token_list
    

 

    def next_token(self) -> Tuple[bool, Optional[str]]:
        if self.pos >= len(self.code):
            return False, None
        
        text = self.code[self.pos:]

        if text.startswith('/*'):
            end_comment_pos = text.find('*/')
            if end_comment_pos == -1:
                line, col = self.char_to_line_col(self.pos)
                self.pos = len(self.code)
                return True, f"Ошибка: незакрытый многострочный комментарий на позиции {line}:{col}"
            else:
                # Пропускаем весь комментарий
                self.pos += end_comment_pos + 2
                return True, None

        # Пропуск однострочных комментариев
        if text.startswith('//'):
            # Пропускаем всю строку
            next_line_pos = text.find('\n')
            if next_line_pos == -1:
                self.pos = len(self.code)  # Конец файла
            else:
                self.pos += next_line_pos + 1
            return True, None

        valid_tokens = [t.name for t in get_token_types_list() if t.class_ in {"keyword", "operator"}]

        for token_type in get_token_types_list():
            regex = re.compile('^' + token_type.regex)
            first_match = regex.match(text)

            if first_match:
                regex_lookahead = re.compile('^' + token_type.regex + r'([^\w\.]|$)')
                lookahead = regex_lookahead.match(text)
                if not lookahead and (token_type.class_ == "keyword" or token_type.class_ == "constant"):
                    continue

                s = ""
                typ = ""
                flag_names = False
                flag_punctuations = False
                flag_operators = False
                flag_keywords = False

                if token_type.class_ == "variable" or token_type.class_ == "constant":
                    temp_s = first_match.group().replace("`", "")
                    if temp_s in self.table_names:
                        s = str(self.table_names[temp_s])
                    else:
                        flag_names = True
                        s = str(self.names_index)
                        self.table_names[temp_s] = self.names_index
                        self.names_index += 1
                    typ = "N"
                
                elif token_type.class_ == "punctuation":
                    if first_match.group() in self.table_punctuations:
                        s = str(self.table_punctuations[first_match.group()])
                    else:
                        flag_punctuations = True
                        s = str(self.punctuations_index)
                        self.table_punctuations[first_match.group()] = self.punctuations_index
                        self.punctuations_index += 1
                    typ = "P"
                
                elif token_type.class_ == "operator":
                    if first_match.group() in self.table_operators:
                        s = str(self.table_operators[first_match.group()])
                    else:
                        flag_operators = True
                        s = str(self.operators_index)
                        self.table_operators[first_match.group()] = self.operators_index
                        self.operators_index += 1
                    typ = "O"
                
                elif token_type.class_ == "keyword":
                    if first_match.group() in self.table_keywords:
                        s = str(self.table_keywords[first_match.group()])
                    else:
                        flag_keywords = True
                        s = str(self.keywords_index)
                        self.table_keywords[first_match.group()] = self.keywords_index
                        self.keywords_index += 1
                    typ = "K"

                line, col = self.char_to_line_col(self.pos)
                new_token = Token(token_type.name, first_match.group(), line, col, f"{typ}:{s}")
                self.pos += len(first_match.group())

                # Обработка скобок
                if token_type.class_ == "punctuation":
                    if first_match.group() in {"(", "{", "["}:
                        self.bracket_stack.append((first_match.group(), line, col))
                    elif first_match.group() in {")", "}", "]"}:
                        if not self.bracket_stack:
                            return True, f"Ошибка: лишняя закрывающая скобка '{first_match.group()}' на позиции {line}:{col}"
                        last_bracket, last_line, last_col = self.bracket_stack.pop()
                        if (last_bracket == "(" and first_match.group() != ")") or (last_bracket == "{" and first_match.group() != "}") or (last_bracket == "[" and first_match.group() != "]"):
                            return True, f"Ошибка: несоответствие скобок '{last_bracket}' и '{first_match.group()}' на позиции {line}:{col}"
                
                if token_type.class_ != "skip":
                    self.token_list.append(new_token)
                
                if token_type.class_ == "keyword" and flag_keywords:
                    self.keywords_token_list.append(new_token)
                elif token_type.class_ == "operator" and flag_operators:
                    self.operators_token_list.append(new_token)
                elif token_type.class_ == "variable" and flag_names:
                    self.names_token_list.append(new_token)
                elif token_type.class_ == "constant" and flag_names:
                    self.names_token_list.append(new_token)
                elif token_type.class_ == "punctuation" and flag_punctuations:
                    self.punctuations_token_list.append(new_token)
                
        
                return True, None
            
         # Если ни один токен не подошёл, ищем возможное исправление через расстояние Левенштейна
        word_candidate = re.match(r'\w+', text)  # Извлекаем возможное слово
        if word_candidate:
            word = word_candidate.group()
            from difflib import get_close_matches
            suggestions = get_close_matches(word, valid_tokens, n=1, cutoff=0.6)  # Ищем похожие токены
            suggestion_msg = f" Возможно, вы имели в виду '{suggestions[0]}'?" if suggestions else ""
            line, col = self.char_to_line_col(self.pos)
            self.pos += len(word) 
            return True, f"Ошибка в позиции {line}:{col}: '{word}' не распознано.{suggestion_msg}"
        
        err_regex = re.compile(r'.*\w|.*$')
        err = err_regex.match(text)
        if err:
            err = err.group().strip()
        line, col = self.char_to_line_col(self.pos)
        self.pos += 1
        return True, f"Position error {line} {col}: {err}"
    

    def char_to_line_col(self, char_index: int) -> Tuple[int, int]:
        if char_index < 0 or char_index >= len(self.code):
            return -1, -1
    
        line = 1
        col = 1

        for i in range(char_index):
            if self.code[i] == '\n':
                line += 1
                col = 1
            else:
                col += 1
        
        return line, col
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Вычисляет расстояние Левенштейна между двумя строками"""
        if len(s1) < len(s2):
            s1, s2 = s2, s1

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]



def get_token_types_list() -> List[TokenType]:
    keywords = [
        TokenType("if", r'if', "keyword"),
        TokenType("else", r'else', "keyword"),
        TokenType("for", r'for', "keyword"),
        TokenType("switch", r'switch', "keyword"),
        TokenType("case", r'case', "keyword"),
        TokenType("default", r'default', "keyword"),
        TokenType("break", r'break', "keyword"),
        TokenType("continue", r'continue', "keyword"),
        TokenType("return", r'return', "keyword"),
        TokenType("func", r'func', "keyword"),
        TokenType("package", r'package', "keyword"),
        TokenType("import", r'import', "keyword"),
        TokenType("var", r'var', "keyword"),
        TokenType("const", r'const', "keyword"),
        TokenType("type", r'type', "keyword"),
        TokenType("struct", r'struct', "keyword"),
        TokenType("interface", r'interface', "keyword"),
        TokenType("go", r'go', "keyword"),
        TokenType("chan", r'chan', "keyword"),
        TokenType("select", r'select', "keyword"),
        TokenType("defer", r'defer', "keyword"),
        TokenType("fallthrough", r'fallthrough', "keyword"),
        TokenType("goto", r'goto', "keyword"),
        TokenType("map", r'map', "keyword"),
        TokenType("range", r'range', "keyword"),
    ]

    operators = [
        TokenType("comparison", r'(==|!=|<|>|<=|>=)', "operator"),
        TokenType("assignment", r'=|\+=|-=|\*=|/=|%=|<<=|>>=|&=|\^=|\\|=', "operator"),
        TokenType("short_declaration", r':=', "operator"),
        TokenType("increment_decrement", r'(\+\+|--)', "operator"),
        TokenType("arithmetic", r'(\+|-|\*|\/|%)', "operator"),
        TokenType("logical", r'(&&|\|\|)', "operator"),
        TokenType("bitwise", r'(&|\||\^|<<|>>)', "operator"),
        TokenType("unary", r'!', "operator"),
    ]

    variables = [
        TokenType("ident", r'[a-zA-Z_]\w*', "variable"),
    ]

    constants = [
        TokenType("integer", r'\d+', "constant"),
        TokenType("float", r'\d+\.\d+', "constant"),
        TokenType("string", r'"[^"]*"', "constant"),
        TokenType("raw_string", r'`[^`]*`', "constant"),
        TokenType("boolean", r'(true|false)', "constant"),
    ]

    punctuations = [
        TokenType("lpar", r'\(', "punctuation"),
        TokenType("rpar", r'\)', "punctuation"),
        TokenType("lbrace", r'\{', "punctuation"),
        TokenType("rbrace", r'\}', "punctuation"),
        TokenType("lbracket", r'\[', "punctuation"),
        TokenType("rbracket", r'\]', "punctuation"),
        TokenType("comma", r',', "punctuation"),
        TokenType("semicolon", r';', "punctuation"),
        TokenType("dot", r'\.', "punctuation"),
        TokenType("colon", r':', "punctuation"),
    ]

    skip = [
        TokenType("SPACE", r'\s', "skip"),
        TokenType("COMMENT", r'//.*|/\*.*?\*/', "skip"),
    ]

    token_types_list = keywords + operators + variables + constants + punctuations + skip
    return token_types_list



    
