with open('templates/home.html', 'r', encoding='utf-8') as f:
    text = f.read()

# If the file starts with a double quote and ends with a double quote, strip them
text = text.strip()
if text.startswith('"') and text.endswith('"'):
    text = text[1:-1]

# Unescape escaped quotes and newlines
text = text.replace('\\"', '"').replace('\\n', '\n').replace('QuizNova ', 'QuizNova —')

with open('templates/home.html', 'w', encoding='utf-8') as out:
    out.write(text)

print('Cleaned up quotes in templates/home.html successfully!')
