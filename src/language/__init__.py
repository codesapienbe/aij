import nltk
import os, sys
import pandas as pd
import numpy as np

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

user_profile = os.environ['USERPROFILE']
SEP = os.path.sep
ENV = os.path.join(user_profile, '.aij', '.env')

def main():

    # if there is at least one argv argument and the name of the argument is "--download", download the data using nltk
    try:    
        if sys.argv and len(sys.argv) > 0 and sys.argv[1] == '--download':
            nltk.download("punkt")
            nltk.download("averaged_perceptron_tagger")
            nltk.download("wordnet")
            nltk.download("stopwords")
            nltk.download("omw-1.4")
            nltk.download("vader_lexicon")
    except IndexError as indexErr: 
        print(
            f"{indexErr.__class__.__name__}: {indexErr}"
        )

    # Tokenization - Breaking text into words or sentences
    text = "Natural language processing is a challenging field, but it can also be very rewarding."
    sentences = nltk.sent_tokenize(text)
    words = nltk.word_tokenize(text)

    pos_tags = nltk.pos_tag(words)

    # Named Entity Recognition - Identifying named entities (such as names, places, and organizations) in text
    ner_tags = nltk.ne_chunk(pos_tags)
    
    # Named Entity Recognition - Identifying named entities (such as names, places, and organizations) in text
    named_entities = nltk.ne_chunk(pos_tags, binary=True)
        
    # if folder does not exist, create it
    if not os.path.exists(os.path.join(user_profile, '.aij', 'language')):
        os.makedirs(os.path.join(user_profile, '.aij', 'language'))
    
    # extract results to csv files
    named_entities_df = pd.DataFrame(named_entities.leaves())
    # add headers id, text, and type
    named_entities_df.columns = ['text', 'type']
    named_entities_df.to_csv(os.path.join(user_profile, '.aij', 'language', 'named_entities.csv'))
    
    # open csv files
    os.startfile(os.path.join(user_profile, '.aij', 'language', 'named_entities.csv'))
    
if __name__ == "__main__":
    main()