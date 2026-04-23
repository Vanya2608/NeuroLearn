import re, pyphen, nltk
from textblob import TextBlob
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
dic = pyphen.Pyphen(lang='en_US')

# Confusing words categories for highlighting
CONFUSING_DICT = {
'homophones': {
'there': 'their/they\'re', 'their': 'there/they\'re', 'they\'re': 'there/their',
'to': 'too/two', 'too': 'to/two', 'two': 'to/too'
},
'visually_similar': {
'was': 'saw', 'saw': 'was',
'from': 'form', 'form': 'from',
'bad': 'dad', 'dad': 'bad'
}
}
def break_syllables(text):
    """Splits words into syllables using a hyphen (e.g., read-ing)."""
    def replace_word(match):
        word = match.group(0)
        if len(word) > 3 and word.isalpha():
            return dic.inserted(word, '-')
        return word
    return re.sub(r'[a-zA-Z]+', replace_word, text)

def highlight_words(text, active_categories):
    """Wraps confusing words in a span with custom data-hint tooltips."""
    def highlight_match(match):
        word = match.group(0)
        lower_w = word.lower()
        for category in active_categories:
            if lower_w in CONFUSING_DICT.get(category, {}):
                hint = CONFUSING_DICT[category][lower_w]
                return f'<span class="highlight hl-{category}" data-hint="Often confused with {hint}">{word}</span>'
        return word
    return re.sub(r'\b[\w\']+\b', highlight_match, text)

def normalize_text(text):
    """Normalizes whitespace and puts each sentence on a new line."""
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = sent_tokenize(text)
    return "\n\n".join(sentences)

def process_dyslexia_text(text, simplify=False, syllables=False,
highlight_categories=None, normalize=False):
    """Main pipeline to apply all text transformations."""
    if not highlight_categories: highlight_categories = []
    if normalize: text = normalize_text(text)
    # Escape HTML to prevent XSS
    processed = text.replace('<', '&lt;').replace('>', '&gt;')
    if syllables: processed = break_syllables(processed)
    if highlight_categories: processed = highlight_words(processed, highlight_categories)
    # Convert newlines to HTML breaks
    return processed.replace('\n', '<br>\n')