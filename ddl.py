from interface import ObjectInterface
import logging

DEF_OPEN = '{'
DEF_CLOSE = '}'

def find_corresponding_close(text, str_open: str, str_close: str, start: int = 0):
    level = 1
    while level > 0:
        first_open = text.find(str_open, start)
        first_close = text.find(str_close, start)

        # Kein Schluss vorhanden
        if first_close < 0:
            return -1
        
        # Öffnen zuerst
        elif first_open < first_close and first_open >= start:
            level += 1
            start = first_open + 1

        # Schließen zuerst
        else:
            level -= 1
            start = first_close + 1
    return first_close

def correct_source_indentation(source: str) -> str:
    lines = [line for line in source.splitlines() if len(line) > 0]
    if len(lines) > 0:
        line_start = len(lines[0]) - len(lines[0].lstrip())
        return '\n'.join(line[line_start:].rstrip() for line in lines)
    else:
        return None

class Interpreter:
    def __init__(self, interface: ObjectInterface) -> None:
        self.interface = interface

    def run(self, text: str):
        start = 0
        valid = True
        while valid:
            first_open = text.find(DEF_OPEN, start)
            first_close = find_corresponding_close(text, DEF_OPEN, DEF_CLOSE, first_open + 1)
            if first_open > 0 and first_close > 0 and first_open < first_close:
                
                # Textelemente auslesen
                indicator = text[start: first_open].strip()
                clear_indicator = indicator.lower().replace(' ', '')
                content = text[first_open + 1: first_close]
                
                # Datentyp erzeugen
                if clear_indicator.startswith('#'):
                    self.__run_datatype_creation__(indicator[1:], content)

                # Attribute erzeugen
                elif clear_indicator == '+attributes':
                    self.__run_attribute_creation__(content)
                
                # Klasse erzeugen
                else:
                    self.__run_class_creation__(indicator, content)

                # Startpunkt hinter das aktuelle Ende setzen
                start = first_close + 1
            else:
                valid = False
        self.interface.log('DDL execution')
        self.interface.commit()
        logging.debug('Structure built')

    def __run_datatype_creation__(self, datatype_name, text: str):
        start = 0
        generator = None
        read_transformer_source = None
        write_transformer_source = None
        valid = True
        while valid:

            # Generator
            if not generator:
                first_comma = text.find(',', start)
                if first_comma > 0:
                    generator = text[start: first_comma].strip()
                    start = first_comma + 1
                else:
                    generator = text.strip()
                    valid = False

            # Transformer Funktionen
            else:
                first_open = text.find(DEF_OPEN, start)
                first_close = find_corresponding_close(text, DEF_OPEN, DEF_CLOSE, first_open + 1)
                if first_open > 0 and first_close > 0 and first_open < first_close:
                    indicator = text[start: first_open].lower().strip()
                    source = correct_source_indentation(text[first_open + 1: first_close])
                    if indicator == 'get':
                        read_transformer_source = source
                    elif indicator == 'set':
                        write_transformer_source = source
                    else:
                        logging.warning(f'Unknown transformer indicator {indicator}')
                    start = first_close + 1
                else:
                    valid = False
        if generator:
            self.interface.create_datatype(datatype_name, generator, read_transformer_source, write_transformer_source)
        else:
            raise SyntaxError('Incorrect datatype definition')

    def __run_attribute_creation__(self, text: str):
        for a in [a.strip() for a in text.split(',')]:
            parameters = [p.strip() for p in a.split(':')]
            self.interface.create_attribute(parameters[0], self.interface.get_datatype(name=parameters[1]))

    def __run_class_creation__(self, class_text: str, content_text: str):
        bracket_open = class_text.find('(')
        bracket_close = class_text.find(')')
        
        # Mit Parent
        if bracket_open > 0 and bracket_close > 0 and bracket_open < bracket_close:
            class_name = class_text[0: bracket_open]
            parent = self.interface.get_class(name=class_text[bracket_open + 1: bracket_close])

        # Ohne Parent
        else:
            class_name = class_text
            parent = None
        class_ = self.interface.create_class(class_name, parent)

        for e in [e.strip() for e in content_text.split(',')]:

            # Referenz
            if e.startswith('~'):
                parameters = [p.strip() for p in e.split('->')]
                reference_name = parameters[0][1:]
                self.interface.create_reference(reference_name, class_, self.interface.get_class(name=parameters[1]))

            # Attributzuweisung
            else:
                parameters = [p.strip() for p in e.split(':')]
                if '*' in parameters[0]:
                    indexed = True
                else:
                    indexed = False
                attribute_name = parameters[0].replace('*', '')
                self.interface.assign_attribute_to_class(class_, self.interface.get_attribute(name=attribute_name), indexed)
