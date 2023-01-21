def reformat_name(name:str):
    replacement_dict = {'_': '\_', '*': '\*', '[': '\[', ']': '\]', '(': '\(',
                    ')': '\)', '~': '\~', '`': '\`', '>': '\>', '#': '\#',
                    '+': '\+', '-': '\-', '=': '\=', '|': '\|', '{': '\{',
                    '}': '\}', '.': '\.', '!': '\!'}
    for i, j in replacement_dict.items():
        name = name.replace(i, j)
    return name


