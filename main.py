import os
from lexer import Lexer, get_token_types_list
from parser import Parser
import json


def main():
    with open("go/product.go", "r") as file:
        code = file.read()

    # Лексический анализ
    lex = Lexer(code)
    tokens = lex.lex_analyze()
    # lex.lex_analyze()

    # Синтаксический анализ
    parser = Parser(tokens=tokens)
    try:
        ast = parser.parse()

        # Запись CST в файл
        with open("results/cst.json", "w", encoding='utf-8') as ast_file:
            json.dump(ast, ast_file, indent=2, ensure_ascii=False)

        # Запись таблицы символов в файл
        with open("results/symbol_table.json", "w", encoding='utf-8') as sym_file:
            json.dump(parser.get_symbol_table(), sym_file, indent=2, ensure_ascii=False)

        # Запись импортов в файл
        with open("results/imports.json", "w", encoding='utf-8') as imp_file:
            json.dump(parser.get_imports(), imp_file, indent=2, ensure_ascii=False)
    
    except Exception as e:
        print(f"Parsing error: {str(e)}")
        print(f"Current token: {parser.current_token().text if parser.current_token() else 'EOF'} at pos {parser.pos}")


    # Запись результатов лексического анализа
    with open("results/result.txt", "w", encoding='cp1251') as main_file, \
         open("results/keywords.txt", "w") as keywords_file, \
         open("results/operators.txt", "w") as operators_file, \
         open("results/names.txt", "w") as names_file, \
         open("results/punctuations.txt", "w") as punctuations_file:

        main_file.write(f"{'Lexeme':<25} {'Token type':<15} {'Row':<5} {'Column':<5} {'Id':<5}\n")
        main_file.write("=========================================================\n")

        keywords_file.write(f"{'Lexeme':<25} {'Token type':<15} {'Row':<5} {'Column':<5} {'Id':<5}\n")
        keywords_file.write("=========================================================\n")

        operators_file.write(f"{'Lexeme':<25} {'Token type':<15} {'Row':<5} {'Column':<5} {'Id':<5}\n")
        operators_file.write("=========================================================\n")

        names_file.write(f"{'Lexeme':<25} {'Token type':<15} {'Row':<5} {'Column':<5} {'Id':<5}\n")
        names_file.write("=========================================================\n")

        punctuations_file.write(f"{'Lexeme':<25} {'Token type':<15} {'Row':<5} {'Column':<5} {'Id':<5}\n")
        punctuations_file.write("=========================================================\n")

        for token in lex.token_list:
            main_file.write(f"{token.text:<25} {token.kind:<15} {token.line:<5} {token.column:<5} {token.id:<5}\n")

        for token in lex.keywords_token_list:
            keywords_file.write(f"{token.text:<25} {token.kind:<15} {token.line:<5} {token.column:<5} {token.id:<5}\n")

        for token in lex.operators_token_list:
            operators_file.write(f"{token.text:<25} {token.kind:<15} {token.line:<5} {token.column:<5} {token.id:<5}\n")

        for token in lex.names_token_list:
            names_file.write(f"{token.text:<25} {token.kind:<15} {token.line:<5} {token.column:<5} {token.id:<5}\n")

        for token in lex.punctuations_token_list:
            punctuations_file.write(f"{token.text:<25} {token.kind:<15} {token.line:<5} {token.column:<5} {token.id:<5}\n")


if __name__ == "__main__":
    main()