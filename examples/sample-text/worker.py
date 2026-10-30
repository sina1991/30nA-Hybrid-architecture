"""Transform a supplied string in the Worker sandbox."""


def run(data, configuration):
    text = data.get('text', 'Hello, 30nA!')
    prefix = configuration.get('prefix', '')
    uppercase = configuration.get('uppercase', False)
    if not isinstance(text, str) or len(text) > 10000 or not isinstance(prefix, str) or len(prefix) > 200 or type(uppercase) is not bool:
        raise ValueError('invalid text configuration')
    result = prefix + (text.upper() if uppercase else text)
    return {'text': result, 'characters': len(result), 'words': len(result.split())}
