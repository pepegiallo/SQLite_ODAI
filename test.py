from accessors import execution

if __name__ == '__main__':
    # Beispiel
    source = """value = calculate(value, 2)"""

    # Code ausführen und 'value' zurückgeben
    result = execution.safe_execute(source)
    print(result)