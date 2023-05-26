import nltk

nltk.download()

# Tokenization - Breaking text into words or sentences
text = "Natural language processing is a challenging field, but it can also be very rewarding."
sentences = nltk.sent_tokenize(text)
words = nltk.word_tokenize(text)

print(sentences)
print(words)
pos_tags = nltk.pos_tag(words)

print(pos_tags)

# Named Entity Recognition - Identifying named entities (such as names, places, and organizations) in text
ner_tags = nltk.ne_chunk(pos_tags)

print(ner_tags)