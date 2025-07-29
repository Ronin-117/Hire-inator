import nltk
from textblob import TextBlob
import re
from nltk.corpus import wordnet


nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

def replace_word(word, pos):
    synonyms = []
    for syn in wordnet.synsets(word, pos=pos):
        for lemma in syn.lemmas():
            if lemma.name().lower() != word.lower():
                synonyms.append(lemma.name())
    if synonyms:
        # Choose the most common synonym based on its frequency in the corpus
        freq_dist = nltk.FreqDist(synonyms)
        most_common_synonym = freq_dist.max()
        return most_common_synonym
    else:
        return word

def clean_symbols(humanized_text):
    # Remove extra spaces and unusual symbol placement
    humanized_text = re.sub(r'\s+', ' ', humanized_text)
    humanized_text = re.sub(r'\s([^\w\s])', r'\1', humanized_text)
    humanized_text = re.sub(r'([^\w\s])\s', r'\1', humanized_text)
    return humanized_text

def humanize_text(text):
    # Split text into sentences while preserving symbols
    # sentences = re.findall(r'[^.!?]+[.!?]+|[^\w\s]|\n', text)
    newline_placeholder = "庄周"
    text = text.replace('\n', newline_placeholder)

    sentences = re.findall(r'[^.!?]+[.!?]+|[^\w\s]+', text)

    # Iterate over each sentence and humanize it
    humanized_sentences = []
    for sentence in sentences:
        # Split sentence into words while preserving symbols
        words = re.findall(r'\w+|[^\w\s]+', sentence)

        # Use TextBlob to get the part-of-speech tags for each word in the sentence
        try:
            tags = TextBlob(sentence).tags
        except Exception as e:
            print(f"Error processing sentence: {e}")
            continue

        # Replace adjectives and adverbs with more human-like alternatives
        humanized_words = []
        for word, tag in tags:
            if tag.startswith('JJ'):
                humanized_word = replace_word(word, 'a')
                humanized_words.append(humanized_word)
            elif tag.startswith('RB'):
                humanized_word = replace_word(word, 'r')
                humanized_words.append(humanized_word)
            else:
                humanized_words.append(word)

        # Join the humanized words back into a sentence with symbols
        humanized_sentence = ''
        for i in range(len(words)):
            if words[i].isalpha() and i < len(humanized_words):
                humanized_sentence += humanized_words[i] + ' '
            else:
                humanized_sentence += words[i]

        humanized_sentences.append(humanized_sentence)


    # Join the humanized sentences back into a single text with symbols
    humanized_text = ''.join(humanized_sentences)

    humanized_text = clean_symbols(humanized_text)
    humanized_text = humanized_text.replace(newline_placeholder, '\n')

    return humanized_text.strip()

# Example usage
ai_generated_text = """Government is one of the most foundational institutions in human civilization. At its core, a government is an organized system by which a community, state, or nation is governed. It is responsible for maintaining order, enforcing laws, ensuring security, and providing essential services to its citizens. Governments exist to manage public resources, settle disputes, and establish frameworks that allow society to function cohesively and peacefully. Without government, societies would lack structure, leading to chaos and lawlessness.

Governments can take various forms depending on the political philosophy and historical context of a country. The most common forms include democracies, monarchies, authoritarian regimes, and communistic systems. In democracies, power is held by the people, either directly or through elected representatives. This system emphasizes participation, individual freedoms, and equal rights. In contrast, authoritarian governments centralize power in the hands of a single ruler or a small elite, often restricting civil liberties. Monarchies, once the dominant form of government, rely on hereditary succession, with power passed down through royal families. Modern monarchies are often constitutional, meaning the monarch's powers are limited by law. Communist governments seek to eliminate class distinctions by placing control of all resources in the hands of the state, ideally representing the will of the working class.

Regardless of its form, every government has a set of fundamental responsibilities. These typically include creating and enforcing laws, protecting the rights of citizens, maintaining public order, defending the country from external threats, and providing public goods such as education, healthcare, transportation infrastructure, and clean water. Governments also regulate the economy, collect taxes, and manage the currency. In doing so, they shape the quality of life for their citizens and the trajectory of national development.

A good government operates transparently and is accountable to its people. In democratic nations, mechanisms such as free press, independent judiciaries, regular elections, and civil society organizations help ensure that government power is checked and balanced. These elements prevent corruption and abuse while empowering citizens to have a voice in how they are governed.

The role of government continues to evolve, especially in the face of global challenges such as climate change, pandemics, economic inequality, and technological disruption. Modern governments must balance national interests with global cooperation, adapt to digital innovation, and meet the growing expectations of an informed and connected populace.

In conclusion, government is an indispensable structure that enables organized society to function. It upholds the rule of law, protects rights, delivers services, and fosters progress. While its form may vary, its purpose remains largely the same: to serve the public good and create conditions where people can live safely, freely, and with dignity."""
print("here's the result!")
humanized_text = humanize_text(ai_generated_text)
print(humanized_text)
