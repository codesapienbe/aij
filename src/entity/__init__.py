import spacy

def get_entities(text):

    # load the pre-trained NER model
    nlp = spacy.load("en_core_web_sm")

    # apply named entity recognition
    doc = nlp(text)

    # extract the entities and their labels
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    return entities

def main():
    
    # sample text
    text = "Bill Gates is the founder of Microsoft Corporation, which is based in Redmond, Washington."

    entities = get_entities(text)

    # print the results
    print("Original text:", text)
    print("Named entities:", entities)
    
    
if __name__ == "__main__":
    main()