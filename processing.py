import re
import pyphen
from textblob import TextBlob
from textblob.wordnet import VERB, ADJ, ADV, NOUN
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

# Initialize Pyphen for syllables
dic = pyphen.Pyphen(lang='en_US')

# Confusing words categories
CONFUSING_DICT = {
    'homophones': {
        'there': 'their/they\'re', 'their': 'there/they\'re', 'they\'re': 'there/their',
        'to': 'too/two', 'too': 'to/two', 'two': 'to/too',
        'your': 'you\'re', 'you\'re': 'your',
        'its': 'it\'s', 'it\'s': 'its',
        'affect': 'effect', 'effect': 'affect',
        'accept': 'except', 'except': 'accept',
        'then': 'than', 'than': 'then',
        'lose': 'loose', 'loose': 'lose',
        'weather': 'whether', 'whether': 'weather',
        'brake': 'break', 'break': 'brake',
        'principal': 'principle', 'principle': 'principal',
        'whose': 'who\'s', 'who\'s': 'whose',
        'aloud': 'allowed', 'allowed': 'aloud'
    },
    'visually_similar': {
        'was': 'saw', 'saw': 'was',
        'from': 'form', 'form': 'from',
        'on': 'no', 'no': 'on',
        'bad': 'dad', 'dad': 'bad',
        'won': 'now', 'now': 'won',
        'stop': 'tops', 'tops': 'stop',
        'god': 'dog', 'dog': 'god'
    },
    'misread': {
        'quit': 'quite/quiet', 'quite': 'quit/quiet', 'quiet': 'quit/quite',
        'desert': 'dessert', 'dessert': 'desert',
        'advice': 'advise', 'advise': 'advice',
        'past': 'passed', 'passed': 'past'
    }
}

# A simple dictionary for some complex word substitutions as an MVP for Text Simplification
COMPLEX_SYNONYMS = {
    'quickly': 'fast',
    'frequently': 'often',
    'enormous': 'huge',
    'fortunate': 'lucky',
    'comprehend': 'understand',
    'utilize': 'use',
    'assist': 'help',
    'commence': 'start',
    'terminate': 'end',
    'sufficient': 'enough',
    'discover': 'find'
}

def simplify_text(text):
    """
    Simplifies complex words based on a simple dictionary mapping.
    Also uses TextBlob to ensure we iterate words properly.
    """
    words = re.findall(r'\b[\w\']+\b', text)
    # Reconstruct text replacing complex synonyms
    for word in words:
        lower_w = word.lower()
        if lower_w in COMPLEX_SYNONYMS:
            # maintain capitalization
            replacement = COMPLEX_SYNONYMS[lower_w]
            if word.istitle():
                replacement = replacement.capitalize()
            elif word.isupper():
                replacement = replacement.upper()
            
            # regex replace the whole word
            pattern = r'\b' + re.escape(word) + r'\b'
            text = re.sub(pattern, replacement, text, count=1)
    return text

def break_syllables(text):
    """
    Breaks words into syllables using pyphen.
    Only breaks words longer than 3 characters.
    """
    # Regex to find words but preserve punctuation
    def replace_word(match):
        word = match.group(0)
        if len(word) > 3 and word.isalpha():
            return dic.inserted(word, '-')
        return word
        
    return re.sub(r'[a-zA-Z]+', replace_word, text)

def highlight_words(text, active_categories):
    """
    Highlights confusing words based on active categories.
    Wraps matched words in a span with a specific class.
    """
    if not active_categories:
        return text

    # Collect all words to highlight into a single processing map
    words_to_highlight = {}
    for category in active_categories:
        if category in CONFUSING_DICT:
            for word, hint in CONFUSING_DICT[category].items():
                words_to_highlight[word.lower()] = (category, hint)
    
    # We want to match whole words and replace them with highlighted span
    # We use a custom substitution function
    def highlight_match(match):
        word = match.group(0)
        lower_w = word.lower()
        if lower_w in words_to_highlight:
            cat, hint = words_to_highlight[lower_w]
            # Replace with a span, giving the category class
            return f'<span class="highlight hl-{cat}" title="Often confused with {hint}">{word}</span>'
        return word
    
    # Since we are returning HTML, we need to carefully replace words without messing up existing HTML
    # Assuming text at this stage has NO html yet, except what we are adding.
    return re.sub(r'\b[\w\']+\b(?!>)', highlight_match, text)

def normalize_text(text):
    """
    Cleans up input text by removing unwanted unicode characters,
    normalizing whitespace, and putting each sentence on a new line.
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Basic unicode cleanup
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Split into sentences using NLTK to provide better pacing
    try:
        sentences = sent_tokenize(text)
        return "\n\n".join(sentences)
    except Exception:
        # Fallback if punkt isn't loaded properly
        return text.replace('. ', '.\n\n')

def advanced_simplify_text(text):
    """
    Advanced simplification: Breaks long sentences containing 'and', 'but'
    or simply uses basic word replacement if advanced parsing is too heavy.
    For this MVP, we do both synonym mapping and long sentence breaking.
    """
    # First apply our simple synonym mapping
    text = simplify_text(text)
    
    # Try breaking sentences at coordinating conjunctions if they are too long
    try:
        sentences = sent_tokenize(text)
        new_sentences = []
        for s in sentences:
            words = word_tokenize(s)
            if len(words) > 15: # Long sentence threshold
                tagged = pos_tag(words)
                # Look for coordinating conjunction after the 5th word
                for i in range(5, len(tagged) - 5):
                    if tagged[i][1] == 'CC' and tagged[i][0].lower() in ['and', 'but']:
                        # Break it into two sentences
                        part1 = " ".join(words[:i]) + "."
                        # capitalize next word
                        part2 = words[i+1].capitalize() + " " +  " ".join(words[i+2:])
                        s = part1 + "\n\n" + part2
                        break
            new_sentences.append(s)
        return "\n\n".join(new_sentences)
    except Exception:
        return text

def process_dyslexia_text(text, simplify=False, syllables=False, highlight_categories=None, normalize=False):
    """ Main pipeline """
    if not highlight_categories:
        highlight_categories = []
        
    if normalize:
        text = normalize_text(text)
        
    # Escape basic HTML to make it safe
    # But wait, we want to return newlines as <br> later too.
    processed = text.replace('<', '&lt;').replace('>', '&gt;')
    
    if simplify:
        processed = advanced_simplify_text(processed)
        
    if syllables:
        processed = break_syllables(processed)
        
    if highlight_categories:
        processed = highlight_words(processed, highlight_categories)
        
    # Convert newlines to breaks
    processed = processed.replace('\n', '<br>\n')
    
    return processed

if __name__ == "__main__":
    # Test
    sample = "The boy who was running quickly over there saw his dad.\nIt was bad weather."
    print("Original:", sample)
    print("Processed:")
    cats = ['homophones', 'visually_similar']
    print(process_dyslexia_text(sample, simplify=True, syllables=True, highlight_categories=cats))
