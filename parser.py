from typing import List, Dict, Any, Optional
from tokenModel import Token

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.token_counter = 0
        self.symbol_table = {
            "scopes": {
                "-Global-": {
                    "constants": {},
                    "variables": {}
                }
            },
            "types": {}
        }
        self.imports = []
        self.current_scope = "-Global-"

    def current_token(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def next_token(self) -> Optional[Token]:
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
    
    def consume_token(self):
        if self.pos < len(self.tokens):
            self.pos += 1
    
    def get_next_token_pos(self) -> int:
        pos = self.token_counter
        self.token_counter += 1
        return pos
    
    def parse_package(self) -> Dict[str, Any]:
        nodes = []
        token = self.current_token()
        if token and token.kind == "package":
            nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            ident = self.current_token()
            if ident and ident.kind == "ident":
                nodes.append({"Name": ident.kind, "Text": ident.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected identifier after 'package'")
            
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected ';' after package declaration")
            
        return {"type": "PackageDeclaration", "nodes": nodes}
    
    def parse_import(self) -> Dict[str, Any]:
        nodes = []
        imports = []
        imports_names = []
        token = self.current_token()

        if token and token.kind == "import":
            nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            has_paren = False
            next_token = self.current_token()
            if next_token and next_token.kind == "lpar":
                has_paren = True
                nodes.append({"Name": next_token.kind, "Text": next_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            
            while self.current_token() and self.current_token().kind == "string":
                import_token = self.current_token()
                self.consume_token()

                semicolon = self.current_token()
                if semicolon and semicolon.kind == "semicolon":
                    imports.append({
                        "package": {"Name": import_token.kind, "Text": import_token.text, "Pos": self.get_next_token_pos()},
                        "semicolon": {"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()}
                    })
                    package_name = import_token.text.strip('"')
                    imports_names.append({"Package": {"Name": package_name, "Pos": self.token_counter - 2}})
                    self.consume_token()
                else:
                    if has_paren and self.current_token() and self.current_token().kind != "rpar":
                        continue  # В многострочном импорте точка с запятой не нужна внутри скобок
                    raise ParseError("Expected ';' after import path")
                
                if not has_paren:
                    break
            
            if has_paren:
                r_paren = self.current_token()
                if r_paren and r_paren.kind == "rpar":
                    nodes.append({"Name": r_paren.kind, "Text": r_paren.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected ')' after import list")
            
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            
            self.imports.extend(imports_names)

        return {"type": "ImportDeclaration", "nodes": nodes, "imports": imports}
    
    def parse_type_declaration(self) -> Optional[Dict[str, Any]]:
        nodes = []
        token = self.current_token()

        if token and token.kind == "type":
            nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            type_name = self.current_token()
            if type_name and type_name.kind == "ident":
                nodes.append({"Name": type_name.kind, "Text": type_name.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected type name after 'type'")

            struct_token = self.current_token()
            if struct_token and struct_token.kind == "struct":
                nodes.append({"Name": struct_token.kind, "Text": struct_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected 'struct' keyword")

            l_brace = self.current_token()
            if l_brace and l_brace.kind == "lbrace":
                nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '{' after 'struct'")

            fields = []
            while self.current_token() and self.current_token().kind != "rbrace":
                field_name = self.current_token()
                if field_name and field_name.kind == "ident":
                    nodes.append({"Name": field_name.kind, "Text": field_name.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                    
                    field_type = self.parse_type()
                    if field_type:
                        field_type_node = {"Name": "Type", "Text": field_type, "Pos": self.get_next_token_pos()}
                        nodes.append(field_type_node)
                        
                        semicolon = self.current_token()
                        if semicolon and semicolon.kind == "semicolon":
                            fields.append({
                                "field_name": {"Name": field_name.kind, "Text": field_name.text, "Pos": self.get_next_token_pos()},
                                "field_type": field_type_node,
                                "semicolon": {"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()}
                            })
                            self.symbol_table["types"].setdefault(type_name.text, {"fields": {}})[
                                "fields"
                            ][field_name.text] = field_type
                            self.consume_token()
                        else:
                            raise ParseError("Expected ';' after field declaration")
                    else:
                        raise ParseError("Expected field type")
                else:
                    raise ParseError("Expected field name")

            r_brace = self.current_token()
            if r_brace and r_brace.kind == "rbrace":
                nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '}' after struct fields")

            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected ';' after '}'")

            return {"type": "TypeDeclaration", "name": type_name.text, "fields": fields, "nodes": nodes}
        return None
    
    def parse_variable_declaration(self, consume_semicolon=True) -> Optional[Dict[str, Any]]:
        nodes = []
        token = self.current_token()
        print(f"Parsing variable declaration at pos {self.pos}: {token.text if token else 'None'} ({token.kind if token else 'None'})")
        
        is_var_declaration = token and token.kind == "var"
        next_tok = self.next_token()
        is_short_declaration = token and token.kind == "ident" and next_tok and next_tok.kind in {"short_declaration", "comma"}

        if not (is_var_declaration or is_short_declaration):
            return None

        if is_var_declaration:
            nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

        var_names = []
        while True:
            var_name = self.current_token()
            if var_name and var_name.kind == "ident":
                var_names.append(var_name)
                nodes.append({"Name": var_name.kind, "Text": var_name.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected variable name")

            comma = self.current_token()
            if comma and comma.kind == "comma":
                nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                break

        var_type = None
        if is_var_declaration:
            # Check if type is explicitly provided (e.g., [10]int)
            type_start = self.current_token()
            if type_start and type_start.kind == "lbracket":
                var_type = self.parse_type()
                if var_type:
                    nodes.append({"Name": "Type", "Text": var_type, "Pos": self.get_next_token_pos()})
            elif type_start and (type_start.kind == "ident" or type_start.kind in self._get_keywords()):
                var_type = self.parse_type()
                if var_type:
                    nodes.append({"Name": "Type", "Text": var_type, "Pos": self.get_next_token_pos()})
            else:
                var_type = "auto"

        assign_token = self.current_token()
        if assign_token and (assign_token.kind == "assignment" or assign_token.kind == "short_declaration"):
            nodes.append({"Name": assign_token.kind, "Text": assign_token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            expr = self.parse_expression()
            nodes.append({"type": "Expression", "value": expr})
            
            # Infer type from expression if not explicitly provided
            if var_type == "auto" and expr["type"] == "ArrayLiteral" and "array_type" in expr:
                var_type = f"[{expr.get('size', '')}]{expr['array_type']}"
            
            scope = self.current_scope or "-Global-"
            for var_name in var_names:
                self.symbol_table["scopes"].setdefault(scope, {"variables": {}, "constants": {}})
                self.symbol_table["scopes"][scope]["variables"][var_name.text] = {
                    "type": var_type or "auto",
                    "pos": self.token_counter,
                    "value": expr
                }
        elif is_var_declaration:
            scope = self.current_scope or "-Global-"
            for var_name in var_names:
                self.symbol_table["scopes"].setdefault(scope, {"variables": {}, "constants": {}})
                self.symbol_table["scopes"][scope]["variables"][var_name.text] = {
                    "type": var_type,
                    "pos": self.token_counter
                }
        else:
            raise ParseError("Expected assignment for short declaration")

        if consume_semicolon:
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            elif semicolon and semicolon.kind != "EOF":
                raise ParseError("Expected ';' after variable declaration")

        return {"type": "VariableDeclaration", "nodes": nodes}
    
    def parse_struct_initialization(self) -> Dict[str, Any]:
        nodes = []
        struct_name = None
        struct_name_str = ""

        # Обрабатываем идентификатор или квалифицированное имя
        current = self.current_token()
        if current and current.kind == "ident":
            struct_name_str = current.text
            nodes.append({"Name": current.kind, "Text": current.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            # Проверяем, есть ли точка (например, product.Product)
            dot = self.current_token()
            if dot and dot.kind == "dot":
                nodes.append({"Name": dot.kind, "Text": dot.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
                next_ident = self.current_token()
                if next_ident and next_ident.kind == "ident":
                    struct_name_str += f".{next_ident.text}"
                    nodes.append({"Name": next_ident.kind, "Text": next_ident.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected identifier after '.'")

        l_brace = self.current_token()
        if l_brace and l_brace.kind == "lbrace":
            nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '{' for struct initialization")

        fields = []
        while self.current_token() and self.current_token().kind != "rbrace":
            field_name = self.current_token()
            if field_name and field_name.kind == "ident":
                nodes.append({"Name": field_name.kind, "Text": field_name.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected struct field name")

            colon = self.current_token()
            if colon and colon.kind == "colon":
                nodes.append({"Name": colon.kind, "Text": colon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected ':' after field name")

            field_value = self.parse_expression()
            fields.append({"name": field_name.text, "value": field_value})

            comma = self.current_token()
            if comma and comma.kind == "comma":
                nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

        r_brace = self.current_token()
        if r_brace and r_brace.kind == "rbrace":
            nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '}' to end struct initialization")

        return {"type": "StructInitialization", "struct_name": struct_name_str, "fields": fields, "nodes": nodes}
    
    def parse_type(self) -> Optional[str]:
        type_token = self.current_token()
        if not type_token:
            return None

        if type_token.kind == "lbracket":
            self.consume_token()
            size_token = self.current_token()
            size = None
            if size_token and size_token.kind == "integer":
                size = size_token.text
                self.consume_token()
            close_bracket = self.current_token()
            if close_bracket and close_bracket.kind == "rbracket":
                self.consume_token()
                array_type = self.parse_type()
                if not array_type:
                    raise ParseError("Expected array element type")
                return f"[{size or ''}]{array_type}"
            else:
                raise ParseError("Expected ']' after array type")
        
        if type_token.kind == "map":
            self.consume_token()
            l_bracket = self.current_token()
            if l_bracket and l_bracket.kind == "lbracket":
                self.consume_token()
            else:
                raise ParseError("Expected '[' after 'map'")
            
            key_type = self.parse_type()
            if not key_type:
                raise ParseError("Expected map key type")
            
            r_bracket = self.current_token()
            if r_bracket and r_bracket.kind == "rbracket":
                self.consume_token()
            else:
                raise ParseError("Expected ']' after map key type")
            
            value_type = self.parse_type()
            if not value_type:
                raise ParseError("Expected map value type")
            
            return f"map[{key_type}]{value_type}"
        
        if type_token.kind in {"ident"} or type_token.kind in self._get_keywords():
            type_name = type_token.text
            self.consume_token()
            
            # Проверяем, есть ли квалифицированное имя (например, package.Type)
            dot = self.current_token()
            if dot and dot.kind == "dot":
                self.consume_token()
                next_ident = self.current_token()
                if next_ident and next_ident.kind == "ident":
                    type_name = f"{type_name}.{next_ident.text}"
                    self.consume_token()
                else:
                    raise ParseError("Expected identifier after '.'")
            
            return type_name
        
        return None
    
    def parse_expression(self) -> Dict[str, Any]:
        current = self.current_token()
        print(f"Parsing expression at pos {self.pos}: {current.text if current else 'None'} ({current.kind if current else 'None'})")
        
        return self.parse_assignment_expression()
        
    def parse_array(self) -> Dict[str, Any]:
        nodes = []
        l_bracket = self.current_token()
        if l_bracket and l_bracket.kind == "lbracket":
            nodes.append({"Name": l_bracket.kind, "Text": l_bracket.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '[' for array")

        # Parse array size (e.g., 10 in [10]int)
        size = None
        size_token = self.current_token()
        if size_token and size_token.kind == "integer":
            size = size_token.text
            nodes.append({"Name": size_token.kind, "Text": size_token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

        r_bracket = self.current_token()
        if r_bracket and r_bracket.kind == "rbracket":
            nodes.append({"Name": r_bracket.kind, "Text": r_bracket.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected ']' for array type")

        # Parse array element type (e.g., int)
        array_type = self.parse_type()
        if not array_type:
            raise ParseError("Expected array element type")
        nodes.append({"Name": "ArrayType", "Text": array_type, "Pos": self.get_next_token_pos()})

        # Parse initialization list (e.g., {1, -2, ...})
        l_brace = self.current_token()
        if l_brace and l_brace.kind == "lbrace":
            nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            # If no initialization list, return type-only array (e.g., for type declarations)
            return {
                "type": "ArrayType",
                "array_type": array_type,
                "size": size,
                "elements": [],
                "nodes": nodes
            }

        elements = []
        while self.current_token() and self.current_token().kind != "rbrace":
            # Handle negative numbers (e.g., -2)
            if self.current_token().kind == "arithmetic" and self.current_token().text == "-":
                self.consume_token()
                number_token = self.current_token()
                if number_token and number_token.kind in {"integer", "float"}:
                    self.consume_token()
                    elements.append({
                        "type": "NumberLiteral",
                        "value": f"-{number_token.text}",
                        "Pos": self.get_next_token_pos()
                    })
                else:
                    raise ParseError("Expected number after '-'")
            elif self.current_token().kind == "lbrace":
                struct = self.parse_struct_initialization()
                elements.append(struct)
            else:
                element = self.parse_expression()
                elements.append(element)

            comma = self.current_token()
            if comma and comma.kind == "comma":
                nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

        r_brace = self.current_token()
        if r_brace and r_brace.kind == "rbrace":
            nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '}' for array initialization")

        return {
            "type": "ArrayLiteral",
            "array_type": array_type,
            "size": size,
            "elements": elements,
            "nodes": nodes
        }
    
    def parse_struct(self) -> Dict[str, Any]:
        return self.parse_struct_initialization()
    
    def parse_assignment_expression(self) -> Dict[str, Any]:
        left = self.parse_comparison_expression()
        operator = self.current_token()
        
        # Поддержка всех операторов присваивания Go
        if operator and operator.kind in {"assignment", "short_declaration"} and operator.text in {"=", ":=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}:
            operator_pos = self.get_next_token_pos()
            self.consume_token()
            right = self.parse_comparison_expression()
            
            # Проверка, является ли правая часть потенциальной инициализацией структуры
            if right["type"] in {"Identifier", "FieldAccess"}:
                next_token = self.current_token()
                if next_token and next_token.kind == "lbrace":
                    self.pos -= 1  # Перемотка для повторного разбора идентификатора или доступа к полю
                    self.token_counter -= 1
                    right = self.parse_struct_initialization()
            
            has_semicolon = False
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                self.consume_token()
                has_semicolon = True
                
            return {
                "type": "AssignmentExpression",
                "left": left,
                "operator": {"type": "Operator", "value": operator.text, "Pos": operator_pos},
                "right": right,
                "semicolon": {"type": "Punctuation", "value": semicolon.text, "Pos": self.get_next_token_pos()} if has_semicolon else None
            }
        return left
    
    def parse_comparison_expression(self) -> Dict[str, Any]:
        left = self.parse_additive_expression()
        
        while True:
            operator = self.current_token()
            if operator and (operator.kind == "comparison" and operator.text in {"==", "!=", "<", ">", "<=", ">="} or
                            operator.kind == "logical" and operator.text in {"&&", "||"}):
                self.consume_token()
                operator_pos = self.get_next_token_pos()
                right = self.parse_additive_expression()
                left = {
                    "type": "BinaryOperation",
                    "left": left,
                    "operator": {"type": "Operator", "value": operator.text, "Pos": operator_pos},
                    "right": right
                }
            else:
                break
        return left
    
    def parse_additive_expression(self) -> Dict[str, Any]:
        left = self.parse_multiplicative_expression()
        
        while True:
            operator = self.current_token()
            if operator and operator.kind == "arithmetic" and operator.text in {"+", "-"}:
                self.consume_token()
                operator_pos = self.get_next_token_pos()
                right = self.parse_multiplicative_expression()
                left = {
                    "type": "BinaryOperation",
                    "left": left,
                    "operator": {"type": "Operator", "value": operator.text, "Pos": operator_pos},
                    "right": right
                }
            else:
                break
        return left
    
    def parse_multiplicative_expression(self) -> Dict[str, Any]:
        left = self.parse_primary_expression()
        
        while True:
            operator = self.current_token()
            if operator and operator.kind == "arithmetic" and operator.text in {"*", "/"}:
                self.consume_token()
                operator_pos = self.get_next_token_pos()
                right = self.parse_primary_expression()
                left = {
                    "type": "BinaryOperation",
                    "left": left,
                    "operator": {"type": "Operator", "value": operator.text, "Pos": operator_pos},
                    "right": right
                }
            else:
                break
        return left
    
    def parse_primary_expression(self) -> Dict[str, Any]:
        token = self.current_token()
        if not token:
            raise ParseError("Unexpected end of input")
        
        print(f"Parsing primary expression at pos {self.pos}: {token.text} ({token.kind})")
        
        if token.kind == "ident":
            identifier = {"type": "Identifier", "value": token.text, "Pos": self.get_next_token_pos()}
            self.consume_token()
            
            # Проверяем, является ли это началом инициализации структуры (например, Store{...})
            next_token = self.current_token()
            if next_token and next_token.kind == "lbrace" and identifier["value"] in self.symbol_table["types"]:
                # Перематываем назад, чтобы parse_struct_initialization обработал идентификатор
                self.pos -= 1
                self.token_counter -= 1
                return self.parse_struct_initialization()
            
            while True:
                next_token = self.current_token()
                if next_token and next_token.kind == "dot":
                    identifier = self.parse_package_or_field_access(identifier)
                    next_token = self.current_token()
                
                elif next_token and next_token.kind == "lbracket":  # Handle index or slice
                    self.consume_token()  # Consume '['
                    nodes = [{"Name": "lbracket", "Text": "[", "Pos": self.get_next_token_pos()}]
                    
                    start_expr = None
                    end_expr = None
                    colon = self.current_token()
                    
                    if colon and colon.kind != "colon" and colon.kind != "rbracket":
                        start_expr = self.parse_expression()
                        nodes.append({"type": "StartExpression", "value": start_expr})
                    
                    colon = self.current_token()
                    if colon and colon.kind == "colon":
                        self.consume_token()
                        nodes.append({"Name": "colon", "Text": ":", "Pos": self.get_next_token_pos()})
                        
                        r_bracket = self.current_token()
                        if r_bracket and r_bracket.kind != "rbracket":
                            end_expr = self.parse_expression()
                            nodes.append({"type": "EndExpression", "value": end_expr})
                    
                    r_bracket = self.current_token()
                    if r_bracket and r_bracket.kind == "rbracket":
                        self.consume_token()
                        nodes.append({"Name": "rbracket", "Text": "]", "Pos": self.get_next_token_pos()})
                    else:
                        raise ParseError("Expected ']' after index or slice")
                    
                    if colon and colon.kind == "colon":
                        identifier = {
                            "type": "SliceExpression",
                            "array": identifier,
                            "start": start_expr,
                            "end": end_expr,
                            "nodes": nodes
                        }
                    else:
                        identifier = {
                            "type": "IndexExpression",
                            "array": identifier,
                            "index": start_expr,
                            "nodes": nodes
                        }
                    next_token = self.current_token()
                
                elif next_token and (next_token.kind == "arithmetic" or next_token.kind == "increment_decrement") and next_token.text in {"++", "--"}:
                    self.consume_token()
                    return {
                        "type": "UnaryOperation",
                        "operator": {"type": "Operator", "value": next_token.text, "Pos": self.get_next_token_pos()},
                        "operand": identifier,
                        "is_prefix": False
                    }
                
                elif next_token and next_token.kind == "lpar":
                    return self.parse_function_call(identifier)
                
                else:
                    break
            
            return identifier
        
        if token.kind == "lbracket":  # Handle array literals
            return self.parse_array()
        
        if token.kind == "arithmetic" and token.text == "-":
            self.consume_token()
            operand = self.parse_primary_expression()
            return {
                "type": "UnaryOperation",
                "operator": {"type": "Operator", "value": "-", "Pos": self.get_next_token_pos()},
                "operand": operand,
                "is_prefix": True
            }
        
        if token.kind == "unary" and token.text == "!":
            self.consume_token()
            operand = self.parse_primary_expression()
            return {
                "type": "UnaryOperation",
                "operator": {"type": "Operator", "value": "!", "Pos": self.get_next_token_pos()},
                "operand": operand,
                "is_prefix": True
            }
        
        if token.kind in {"arithmetic", "increment_decrement"} and token.text in {"++", "--"}:
            operator = token.text
            self.consume_token()
            operand = self.parse_primary_expression()
            return {
                "type": "UnaryOperation",
                "operator": {"type": "Operator", "value": operator, "Pos": self.get_next_token_pos()},
                "operand": operand,
                "is_prefix": True
            }
        
        if token.kind == "integer":
            self.consume_token()
            return {"type": "NumberLiteral", "value": token.text, "Pos": self.get_next_token_pos()}
        if token.kind == "float":
            self.consume_token()
            return {"type": "NumberLiteral", "value": token.text, "Pos": self.get_next_token_pos()}
        if token.kind in {"string", "raw_string"}:  # Поддержка raw_string
            self.consume_token()
            return {"type": "StringLiteral", "value": token.text, "Pos": self.get_next_token_pos()}
        if token.kind == "lpar":
            self.consume_token()
            expr = self.parse_expression()
            r_paren = self.current_token()
            if r_paren and r_paren.kind == "rpar":
                self.consume_token()
                return expr
            raise ParseError("Expected ')' after expression")
        
        raise ParseError(f"Unexpected token: {token.text}")
    
    def parse_package_or_field_access(self, identifier: Dict[str, Any]) -> Dict[str, Any]:
        self.consume_token()  # Skip dot
        field_or_func = self.current_token()
        if field_or_func and field_or_func.kind == "ident":
            self.consume_token()
            next_token = self.current_token()
            if next_token and next_token.kind == "lpar":
                return self.parse_function_call({
                    "type": "PackageCall",
                    "package": identifier,
                    "function": {"type": "Identifier", "value": field_or_func.text, "Pos": self.get_next_token_pos()}
                })
            return {
                "type": "FieldAccess",
                "object": identifier,
                "field": {"type": "Identifier", "value": field_or_func.text, "Pos": self.get_next_token_pos()}
            }
        raise ParseError("Expected field or function name after dot")
    
    def parse_function_call(self, function_info: Dict[str, Any]) -> Dict[str, Any]:
        print(f"Parsing function call: {function_info}")
        nodes = []
        package_name = None
        function_name = function_info["value"] if "value" in function_info else function_info["function"]["value"]
        if function_info["type"] == "PackageCall":
            package_name = function_info["package"]["value"]

        l_paren = self.current_token()
        if l_paren and l_paren.kind == "lpar":
            nodes.append({"Name": l_paren.kind, "Text": l_paren.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '(' after function name")

        args = []
        if function_name == "make":
            type_arg = self.parse_type()
            if not type_arg:
                raise ParseError("Expected type argument for 'make'")
            args.append({"type": "Type", "value": type_arg})
            
            comma = self.current_token()
            if comma and comma.kind == "comma":
                nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
                while self.current_token() and self.current_token().kind != "rpar":
                    arg = self.parse_expression()
                    args.append(arg)
                    comma = self.current_token()
                    if comma and comma.kind == "comma":
                        nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                        self.consume_token()
        else:
            while self.current_token() and self.current_token().kind != "rpar":
                arg = self.parse_expression()
                args.append(arg)
                
                comma = self.current_token()
                if comma and comma.kind == "comma":
                    nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()

        r_paren = self.current_token()
        if r_paren and r_paren.kind == "rpar":
            nodes.append({"Name": r_paren.kind, "Text": r_paren.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected ')' after function arguments")

        return {"type": "FunctionCall", "package": package_name, "name": function_name, "args": args, "nodes": nodes}
    

    def parse_if_statement(self) -> Optional[Dict[str, Any]]:
        token = self.current_token()
        if not token or token.kind != "if":
            return None

        nodes = []
        nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
        self.consume_token()

        # Условие if
        condition = self.parse_expression()
        nodes.append({"type": "Condition", "value": condition})

        # Открывающая фигурная скобка блока then
        l_brace = self.current_token()
        if l_brace and l_brace.kind == "lbrace":
            nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '{' after if condition")

        # Тело блока then
        then_body = []
        while self.current_token() and self.current_token().kind != "rbrace":
            stmt = self.parse_statement()
            if stmt:
                then_body.append(stmt)
            else:
                raise ParseError("Expected statement in if block")

        r_brace = self.current_token()
        if r_brace and r_brace.kind == "rbrace":
            nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '}' after if block")

        # Проверка на else
        else_body = []
        else_token = self.current_token()
        if else_token and else_token.kind == "else":
            nodes.append({"Name": else_token.kind, "Text": else_token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            l_brace = self.current_token()
            if l_brace and l_brace.kind == "lbrace":
                nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '{' after else")

            while self.current_token() and self.current_token().kind != "rbrace":
                stmt = self.parse_statement()
                if stmt:
                    else_body.append(stmt)
                else:
                    raise ParseError("Expected statement in else block")

            r_brace = self.current_token()
            if r_brace and r_brace.kind == "rbrace":
                nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '}' after else block")

        return {
            "type": "IfStatement",
            "condition": condition,
            "then": then_body,
            "else": else_body if else_body else None,
            "nodes": nodes
        }
    

    def parse_for_statement(self) -> Optional[Dict[str, Any]]:
        token = self.current_token()
        if not token or token.kind != "for":
            return None

        nodes = []
        nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
        self.consume_token()

        # Проверяем, является ли это циклом range
        init_stmt = None
        condition = None
        post_stmt = None
        range_stmt = None
        next_tok = self.current_token()

        if next_tok and next_tok.kind == "ident":
            # Проверяем, есть ли short_declaration или comma (для range)
            next_next_tok = self.next_token()
            if next_next_tok and next_next_tok.kind in {"short_declaration", "comma"}:
                # Это может быть range или обычная инициализация
                var_names = []
                var_positions = []  # Сохраняем позиции токенов
                while True:
                    var_name = self.current_token()
                    if var_name and var_name.kind == "ident":
                        var_pos = self.get_next_token_pos()
                        var_names.append(var_name)
                        var_positions.append(var_pos)
                        nodes.append({"Name": var_name.kind, "Text": var_name.text, "Pos": var_pos})
                        self.consume_token()
                    else:
                        break

                    comma = self.current_token()
                    if comma and comma.kind == "comma":
                        nodes.append({"Name": comma.kind, "Text": comma.text, "Pos": self.get_next_token_pos()})
                        self.consume_token()
                    else:
                        break

                assign_token = self.current_token()
                if assign_token and assign_token.kind == "short_declaration":
                    assign_pos = self.get_next_token_pos()
                    nodes.append({"Name": assign_token.kind, "Text": assign_token.text, "Pos": assign_pos})
                    self.consume_token()

                    # Проверяем, является ли это range
                    range_token = self.current_token()
                    if range_token and range_token.kind == "range":
                        nodes.append({"Name": range_token.kind, "Text": range_token.text, "Pos": self.get_next_token_pos()})
                        self.consume_token()

                        # Разбираем выражение после range
                        range_expr = self.parse_expression()
                        nodes.append({"type": "RangeExpression", "value": range_expr})

                        scope = self.current_scope or "-Global-"
                        for var_name in var_names:
                            self.symbol_table["scopes"].setdefault(scope, {"variables": {}, "constants": {}})
                            self.symbol_table["scopes"][scope]["variables"][var_name.text] = {
                                "type": "auto",
                                "pos": self.token_counter
                            }

                        range_stmt = {
                            "type": "RangeStatement",
                            "variables": [
                                {"type": "Identifier", "value": var_name.text, "Pos": var_pos}
                                for var_name, var_pos in zip(var_names, var_positions)
                            ],
                            "expression": range_expr
                        }
                    else:
                        # Обычная инициализация
                        expr = self.parse_expression()
                        nodes.append({"type": "Expression", "value": expr})

                        scope = self.current_scope or "-Global-"
                        for var_name in var_names:
                            self.symbol_table["scopes"].setdefault(scope, {"variables": {}, "constants": {}})
                            self.symbol_table["scopes"][scope]["variables"][var_name.text] = {
                                "type": "auto",
                                "pos": self.token_counter,
                                "value": expr
                            }

                        init_stmt = {
                            "type": "VariableDeclaration",
                            "nodes": [
                                {"Name": var_name.kind, "Text": var_name.text, "Pos": var_pos}
                                for var_name, var_pos in zip(var_names, var_positions)
                            ] + [
                                {"Name": assign_token.kind, "Text": assign_token.text, "Pos": assign_pos},
                                {"type": "Expression", "value": expr}
                            ]
                        }

                        # Ожидаем точку с запятой после инициализации
                        semicolon1 = self.current_token()
                        if semicolon1 and semicolon1.kind == "semicolon":
                            nodes.append({"Name": semicolon1.kind, "Text": semicolon1.text, "Pos": self.get_next_token_pos()})
                            self.consume_token()
                        else:
                            raise ParseError(f"Expected ';' after for initialization, got {semicolon1.text if semicolon1 else 'None'} at pos {self.pos}")

                        # Условие (опционально)
                        if self.current_token() and self.current_token().kind != "semicolon":
                            condition = self.parse_expression()
                            nodes.append({"type": "Condition", "value": condition})

                        # Вторая точка с запятой после условия
                        semicolon2 = self.current_token()
                        if semicolon2 and semicolon2.kind == "semicolon":
                            nodes.append({"Name": semicolon2.kind, "Text": semicolon2.text, "Pos": self.get_next_token_pos()})
                            self.consume_token()
                        else:
                            raise ParseError(f"Expected ';' after for condition, got {semicolon2.text if semicolon2 else 'None'} at pos {self.pos}")

                        # Пост-действие (опционально)
                        if self.current_token() and self.current_token().kind != "lbrace":
                            post_stmt = self.parse_expression()
                            nodes.append({"type": "Post", "value": post_stmt})
                else:
                    # Обычная инициализация через выражение
                    init_stmt = self.parse_expression()
                    nodes.append({"type": "Init", "value": init_stmt})

                    # Ожидаем точку с запятой после выражения
                    semicolon1 = self.current_token()
                    if semicolon1 and semicolon1.kind == "semicolon":
                        nodes.append({"Name": semicolon1.kind, "Text": semicolon1.text, "Pos": self.get_next_token_pos()})
                        self.consume_token()
                    else:
                        raise ParseError(f"Expected ';' after for initialization, got {semicolon1.text if semicolon1 else 'None'} at pos {self.pos}")

                    # Условие (опционально)
                    if self.current_token() and self.current_token().kind != "semicolon":
                        condition = self.parse_expression()
                        nodes.append({"type": "Condition", "value": condition})

                    # Вторая точка с запятой после условия
                    semicolon2 = self.current_token()
                    if semicolon2 and semicolon2.kind == "semicolon":
                        nodes.append({"Name": semicolon2.kind, "Text": semicolon2.text, "Pos": self.get_next_token_pos()})
                        self.consume_token()
                    else:
                        raise ParseError(f"Expected ';' after for condition, got {semicolon2.text if semicolon2 else 'None'} at pos {self.pos}")

                    # Пост-действие (опционально)
                    if self.current_token() and self.current_token().kind != "lbrace":
                        post_stmt = self.parse_expression()
                        nodes.append({"type": "Post", "value": post_stmt})

            elif next_tok and next_tok.kind == "semicolon":
                # Пустая инициализация
                nodes.append({"Name": next_tok.kind, "Text": next_tok.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

                # Условие (опционально)
                if self.current_token() and self.current_token().kind != "semicolon":
                    condition = self.parse_expression()
                    nodes.append({"type": "Condition", "value": condition})

                # Вторая точка с запятой после условия
                semicolon2 = self.current_token()
                if semicolon2 and semicolon2.kind == "semicolon":
                    nodes.append({"Name": semicolon2.kind, "Text": semicolon2.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError(f"Expected ';' after for condition, got {semicolon2.text if semicolon2 else 'None'} at pos {self.pos}")

                # Пост-действие (опционально)
                if self.current_token() and self.current_token().kind != "lbrace":
                    post_stmt = self.parse_expression()
                    nodes.append({"type": "Post", "value": post_stmt})

            # Открывающая фигурная скобка тела цикла
            l_brace = self.current_token()
            if l_brace and l_brace.kind == "lbrace":
                nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '{' after for clause")

            # Тело цикла
            body = []
            while self.current_token() and self.current_token().kind != "rbrace":
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
                else:
                    raise ParseError("Expected statement in for body")

            r_brace = self.current_token()
            if r_brace and r_brace.kind == "rbrace":
                nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '}' after for body")

            return {
                "type": "ForStatement",
                "init": init_stmt,
                "condition": condition,
                "post": post_stmt,
                "range": range_stmt,
                "body": body,
                "nodes": nodes
            }


    def parse_expression_list(self) -> List[Dict[str, Any]]:
        expressions = []
        while self.current_token() and self.current_token().kind not in {"semicolon", "rbrace", "EOF"}:
            expr = self.parse_expression()
            expressions.append(expr)
            
            comma = self.current_token()
            if comma and comma.kind == "comma":
                self.consume_token()
            else:
                break
        return expressions


    def parse_switch_statement(self) -> Optional[Dict[str, Any]]:
        token = self.current_token()
        if not token or token.kind != "switch":
            return None

        nodes = []
        nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
        self.consume_token()

        # Проверяем, есть ли выражение switch (опционально)
        expr = None
        next_token = self.current_token()
        if next_token and next_token.kind not in {"lbrace", "semicolon", "EOF"}:
            expr = self.parse_expression()
            nodes.append({"type": "Expression", "value": expr})

        # Открывающая фигурная скобка
        l_brace = self.current_token()
        if l_brace and l_brace.kind == "lbrace":
            nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '{' after switch")

        # Разбор веток case и default
        cases = []
        default_case = None
        while self.current_token() and self.current_token().kind != "rbrace":
            case_token = self.current_token()
            if case_token and case_token.kind == "case":
                nodes.append({"Name": case_token.kind, "Text": case_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

                # Разбор условия case
                conditions = self.parse_expression_list()
                if not conditions:
                    raise ParseError("Expected condition after 'case'")
                nodes.append({"type": "CaseConditions", "value": conditions})

                # Проверяем двоеточие
                colon = self.current_token()
                if colon and colon.kind == "colon":
                    nodes.append({"Name": colon.kind, "Text": colon.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected ':' after case condition")

                # Разбор тела case
                body = []
                while self.current_token() and self.current_token().kind not in {"case", "default", "rbrace"}:
                    stmt = self.parse_statement()
                    if stmt:
                        body.append(stmt)
                    else:
                        raise ParseError("Expected statement in case block")

                cases.append({
                    "type": "CaseClause",
                    "conditions": conditions,
                    "body": body
                })

            elif case_token and case_token.kind == "default":
                if default_case is not None:
                    raise ParseError("Multiple 'default' clauses are not allowed")
                nodes.append({"Name": case_token.kind, "Text": case_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

                # Проверяем двоеточие
                colon = self.current_token()
                if colon and colon.kind == "colon":
                    nodes.append({"Name": colon.kind, "Text": colon.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected ':' after default")

                # Разбор тела default
                body = []
                while self.current_token() and self.current_token().kind not in {"case", "default", "rbrace"}:
                    stmt = self.parse_statement()
                    if stmt:
                        body.append(stmt)
                    else:
                        raise ParseError("Expected statement in default block")

                default_case = {
                    "type": "DefaultClause",
                    "body": body
                }

            else:
                raise ParseError(f"Expected 'case' or 'default', got {case_token.text}")

        # Закрывающая фигурная скобка
        r_brace = self.current_token()
        if r_brace and r_brace.kind == "rbrace":
            nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
            self.consume_token()
        else:
            raise ParseError("Expected '}' after switch cases")

        return {
            "type": "SwitchStatement",
            "expression": expr,
            "cases": cases,
            "default": default_case,
            "nodes": nodes
        }


    def parse_statement(self) -> Optional[Dict[str, Any]]:
        token = self.current_token()
        if not token:
            return None
            
        print(f"Parsing statement at pos {self.pos}: {token.text} ({token.kind})")
        if token.kind == "for":
            return self.parse_for_statement()
        if token.kind == "if":
            return self.parse_if_statement()
        if token.kind == "switch":
            return self.parse_switch_statement()
        if token.kind == "continue":
            nodes = [{"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()}]
            self.consume_token()
            return {"type": "ContinueStatement", "nodes": nodes}
        if token.kind == "break":
            nodes = [{"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()}]
            self.consume_token()
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                self.consume_token()
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
            return {"type": "BreakStatement", "nodes": nodes}
        if token.kind == "return":
            nodes = [{"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()}]
            self.consume_token()
            expressions = []
            next_token = self.current_token()
            if next_token and next_token.kind not in {"semicolon", "rbrace", "EOF"}:
                expressions = self.parse_expression_list()
                for expr in expressions:
                    nodes.append({"type": "Expression", "value": expr})
            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                self.consume_token()
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
            return {"type": "ReturnStatement", "expressions": expressions, "nodes": nodes}
        if token.kind == "var" or (token.kind == "ident" and self.next_token() and self.next_token().kind in {"short_declaration", "comma"}):
            return self.parse_variable_declaration(consume_semicolon=True)
        expr = self.parse_expression()
        semicolon = self.current_token()
        if semicolon and semicolon.kind == "semicolon":
            self.consume_token()
            expr["semicolon"] = {"type": "Punctuation", "value": semicolon.text, "Pos": self.get_next_token_pos()}
        return expr

    def parse_function(self) -> Optional[Dict[str, Any]]:
        nodes = []
        token = self.current_token()
        
        if token and token.kind == "func":
            print(f"Parsing function at pos {self.pos}: {token.text}")
            nodes.append({"Name": token.kind, "Text": token.text, "Pos": self.get_next_token_pos()})
            self.consume_token()

            receiver = None
            # Проверяем, есть ли получатель (например, (s Store))
            next_token = self.current_token()
            if next_token and next_token.kind == "lpar":
                nodes.append({"Name": next_token.kind, "Text": next_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

                receiver_name = self.current_token()
                if receiver_name and receiver_name.kind == "ident":
                    receiver_name_text = receiver_name.text
                    nodes.append({"Name": receiver_name.kind, "Text": receiver_name.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected receiver name after '('")

                receiver_type = self.parse_type()
                if not receiver_type:
                    raise ParseError("Expected receiver type")

                nodes.append({"Name": "Type", "Text": receiver_type, "Pos": self.get_next_token_pos()})

                r_paren = self.current_token()
                if r_paren and r_paren.kind == "rpar":
                    nodes.append({"Name": r_paren.kind, "Text": r_paren.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected ')' after receiver")

                receiver = {
                    "name": receiver_name_text,
                    "type": receiver_type
                }

            func_name = self.current_token()
            if func_name and func_name.kind == "ident":
                nodes.append({"Name": func_name.kind, "Text": func_name.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected function name after 'func' or receiver")

            self.current_scope = func_name.text

            l_paren = self.current_token()
            if l_paren and l_paren.kind == "lpar":
                nodes.append({"Name": l_paren.kind, "Text": l_paren.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '(' after function name")

            params = []
            while self.current_token() and self.current_token().kind != "rpar":
                param_names = []
                while self.current_token() and self.current_token().kind == "ident":
                    param_name = self.current_token()
                    param_names.append(param_name)
                    self.consume_token()
                    
                    comma = self.current_token()
                    if comma and comma.kind == "comma":
                        self.consume_token()
                    else:
                        break
                
                param_type = self.parse_type()
                if not param_type:
                    raise ParseError("Expected parameter type")

                for param_name in param_names:
                    self.symbol_table["scopes"].setdefault(func_name.text, {"variables": {}, "constants": {}})
                    self.symbol_table["scopes"][func_name.text]["variables"][param_name.text] = {
                        "type": param_type,
                        "pos": self.token_counter
                    }
                    params.append({
                        "param_name": {"Name": param_name.kind, "Text": param_name.text, "Pos": self.get_next_token_pos()},
                        "param_type": param_type
                    })

                comma = self.current_token()
                if comma and comma.kind == "comma":
                    self.consume_token()

            r_paren = self.current_token()
            if r_paren and r_paren.kind == "rpar":
                nodes.append({"Name": r_paren.kind, "Text": r_paren.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected ')' after parameters")

            return_types = []
            return_token = self.current_token()
            if return_token and return_token.kind == "lpar":
                nodes.append({"Name": return_token.kind, "Text": return_token.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
                
                while self.current_token() and self.current_token().kind != "rpar":
                    return_type = self.parse_type()
                    if return_type:
                        return_types.append(return_type)
                    else:
                        raise ParseError("Expected return type")
                    
                    comma = self.current_token()
                    if comma and comma.kind == "comma":
                        self.consume_token()
                
                r_paren_return = self.current_token()
                if r_paren_return and r_paren_return.kind == "rpar":
                    nodes.append({"Name": r_paren_return.kind, "Text": r_paren_return.text, "Pos": self.get_next_token_pos()})
                    self.consume_token()
                else:
                    raise ParseError("Expected ')' after return types")
            elif return_token and (return_token.kind in self._get_keywords() or return_token.kind == "ident"):
                return_type = self.parse_type()
                if return_type:
                    return_types.append(return_type)

            l_brace = self.current_token()
            if l_brace and l_brace.kind == "lbrace":
                nodes.append({"Name": l_brace.kind, "Text": l_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '{' after function declaration")

            body = []
            while self.current_token() and self.current_token().kind != "rbrace":
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)

            r_brace = self.current_token()
            if r_brace and r_brace.kind == "rbrace":
                nodes.append({"Name": r_brace.kind, "Text": r_brace.text, "Pos": self.get_next_token_pos()})
                self.consume_token()
            else:
                raise ParseError("Expected '}' after function body")

            semicolon = self.current_token()
            if semicolon and semicolon.kind == "semicolon":
                nodes.append({"Name": semicolon.kind, "Text": semicolon.text, "Pos": self.get_next_token_pos()})
                self.consume_token()

            self.current_scope = "-Global-"
            print(f"Finished parsing function at pos {self.pos}")

            return {
                "type": "FunctionDeclaration",
                "name": func_name.text,
                "receiver": receiver,
                "params": params,
                "return_types": return_types,
                "body": body,
                "nodes": nodes
            }
        return None

    def _get_keywords(self) -> List[str]:
        return [
            "bool", "string", "int", "int8", "int16", "int32", "int64",
            "uint", "uint8", "uint16", "uint32", "uint64", "float32", "float64"
        ]
    
    def parse(self) -> Dict[str, Any]:
        children = []
        
        while self.current_token():
            token = self.current_token()
            print(f"Parsing token at pos {self.pos}: {token.text} ({token.kind})")
            if token.kind == "package":
                children.append(self.parse_package())
            elif token.kind == "import":
                children.append(self.parse_import())
            elif token.kind == "type":
                type_decl = self.parse_type_declaration()
                if type_decl:
                    children.append(type_decl)
            elif token.kind == "func":
                func_decl = self.parse_function()
                if func_decl:
                    children.append(func_decl)
            elif token.kind == "ident":
                var_decl = self.parse_variable_declaration()
                if var_decl:
                    children.append(var_decl)
                else:
                    self.consume_token()
            elif token.kind == "EOF":
                break
            else:
                self.consume_token()

        return {"type": "Program", "children": children}

    def get_symbol_table(self) -> Dict[str, Any]:
        return self.symbol_table

    def get_imports(self) -> List[Dict[str, Any]]:
        return self.imports
    