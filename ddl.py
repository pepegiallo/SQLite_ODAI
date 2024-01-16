from interface import ObjectInterface
import logging

class Interpreter:
    def __init__(self, interface: ObjectInterface) -> None:
        self.interface = interface

    def run(self, text: str):
        start = 0
        valid = True
        while valid:
            first_open = text.find('{', start)
            first_close = text.find('}', start)
            if first_open > 0 and first_close > 0 and first_open < first_close:
                
                # Textelemente auslesen
                indicator = text[start: first_open].strip()
                clear_indicator = indicator.lower().replace(' ', '')
                content = text[first_open + 1: first_close]
                
                # Attribute erzeugen
                if clear_indicator == '+attributes':
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

    def __run_attribute_creation__(self, text: str):
        for a in [a.strip() for a in text.split(',')]:
            parameters = [p.strip() for p in a.split(':')]
            self.interface.create_attribute(parameters[0], parameters[1])

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
                if '!' in parameters[0]:
                    nullable = False
                else:
                    nullable = True
                if len(parameters) > 1:
                    default = parameters[1]
                else:
                    default = None
                attribute_name = parameters[0].replace('*', '').replace('!', '')
                self.interface.assign_attribute_to_class(class_, self.interface.get_attribute(name=attribute_name), indexed, nullable, default)
