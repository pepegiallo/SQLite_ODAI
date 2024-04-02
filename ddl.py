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
    
def parse_tagged_name(name: str, tag_character: str = '*'):
    if tag_character in name:
        return name.replace(tag_character, ''), True
    else:
        return name, False

class Interpreter:
    def __init__(self, interface: ObjectInterface) -> None:
        self.interface = interface

    def run(self, text: str):
        """ Run ddl script """
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
        """ Creates new datatype with the given name and ddl text """
        start = 0
        indicator = None
        generator = None
        parent_name = None
        read_transformer_source = None
        write_transformer_source = None
        valid = True
        while valid:

            # Generator / Parent
            if not (generator or parent_name):
                first_comma = text.find(',', start)
                if first_comma > 0:
                    indicator = text[start: first_comma].strip()
                    start = first_comma + 1
                else:
                    indicator = text.strip()
                    valid = False
                if indicator.startswith('#'):
                    parent_name = indicator[1:]
                else:
                    generator = indicator

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
            self.interface.create_datatype(datatype_name, 
                                           read_transformer_source=read_transformer_source, 
                                           write_transformer_source=write_transformer_source, 
                                           generator=generator)
        elif parent_name:
            self.interface.create_datatype(datatype_name, 
                                           read_transformer_source=read_transformer_source, 
                                           write_transformer_source=write_transformer_source, 
                                           parent=self.interface.get_datatype(parent_name))
        else:
            raise SyntaxError('Incorrect datatype definition')

    def __run_attribute_creation__(self, text: str):
        """ Run attribute creation with the given ddl text """
        for a in [a.strip() for a in text.split(',')]:
            parameters = [p.strip() for p in a.split(':')]
            self.interface.create_attribute(parameters[0], self.interface.get_datatype(parameters[1]))

    def __run_class_creation__(self, class_text: str, content_text: str):
            bracket_open = class_text.find('(')
            bracket_close = class_text.find(')')
            
            # Mit Parent
            if bracket_open > 0 and bracket_close > 0 and bracket_open < bracket_close:
                class_name, traced = parse_tagged_name(class_text[0: bracket_open])
                parent = self.interface.get_class(class_text[bracket_open + 1: bracket_close])

            # Ohne Parent
            else:
                class_name, traced = parse_tagged_name(class_text)
                parent = None
            class_ = self.interface.create_class(class_name, traced, parent)

            # Attribute und Referenzen
            start = 0
            valid = True
            while valid:

                # Ende des Elements finden und Elementtext extrahieren
                first_comma = content_text.find(',', start)
                first_open = content_text.find(DEF_OPEN, start)

                # Kein Komma und kein Transformer => Letztes Element
                if first_comma < 0 and first_open < 0:
                    element_text = content_text[start:]
                    valid = False

                # Nur Komma gefunden oder Komma vor Transformer => Element ohne Transformer
                elif first_comma >= 0 and first_open < 0 or first_comma < first_open:
                    element_text = content_text[start: first_comma]
                    start = first_comma + 1

                # Sonst => Element mit Transformer
                else:
                    first_close = find_corresponding_close(content_text, DEF_OPEN, DEF_CLOSE, first_open + 1)
                    element_text = content_text[start: first_close]
                    next_comma = content_text.find(',', first_close)
                    
                    # Letztes Element?
                    if next_comma < 0:
                        valid = False
                    else:
                        start = next_comma + 1

                # Referenz
                if element_text.strip().startswith('~'):
                    self.__run_reference_creation__(element_text, class_)

                # Attributzuweisung
                else:
                    self.__run_attribute_assignment__(element_text, class_)

    def __run_reference_creation__(self, text: str, class_):
        """ Create new reference with the given ddl text at the given class """
        parameters = [p.strip() for p in text.split('->')]
        reference_name = parameters[0][1:]
        bracket_open = parameters[1].find('(')
        bracket_close = parameters[1].find(')')
        if bracket_open > 0 and bracket_close > 0:
            if bracket_open < bracket_close:
                target_class_name = parameters[1][:bracket_open]
                cardinality = int(parameters[1][bracket_open + 1: bracket_close])
            else:
                raise SyntaxError(f'Incorrect reference definition ({parameters[0]})')
        else:
            target_class_name = parameters[1]
            cardinality = None
        self.interface.create_reference(reference_name, class_, self.interface.get_class(target_class_name), cardinality)

    def __run_attribute_assignment__(self, text: str, class_):
        """ Assigns an existing attribute by the given ddl text to the given class """
        read_transformer_source = None
        write_transformer_source = None
        start = 0
        first_open = text.find(DEF_OPEN, start)

        # Keine Transformer funktionen
        if first_open < 0:
            attribute_text = text.strip()

        # Transformer funktionen
        else:
            attribute_text = text[start: first_open].strip()
            start = first_open + 1
            valid = True
            while valid:
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

        # Attribut zuweisen
        attribute_name = attribute_text.replace('*', '')
        indexed = len(attribute_text) > len(attribute_name)
        self.interface.assign_attribute_to_class(class_, self.interface.get_attribute(attribute_name), indexed, read_transformer_source, write_transformer_source)
