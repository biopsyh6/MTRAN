class Token:
    def __init__(self, kind: str, text: str, line: int, column: int, id: str):
        self.kind = kind
        self.text = text
        self.line = line
        self.column = column
        self.id = id

class TokenType:
    def __init__(self, name: str, regex: str, class_:str):
        self.name = name
        self.regex = regex
        self.class_ = class_
        