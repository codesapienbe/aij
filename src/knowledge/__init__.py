# Define a knowledge base as a dictionary
knowledge_base = {
    "artificial intelligence": ["AI", "machine learning", "neural networks"],
    "climate change": ["global warming", "greenhouse gases", "carbon emissions"],
    "COVID-19": ["coronavirus", "pandemic", "vaccine"],
    # and so on...
}

# Define a function that takes a topic and returns related terms from the knowledge base
def get_related_terms(topic):
    if topic in knowledge_base:
        return knowledge_base[topic]
    else:
        return []
    
def main():

    # Test the function with a few different topics
    print(get_related_terms("artificial intelligence"))

    print(get_related_terms("COVID-19"))

    print(get_related_terms("space exploration"))
    
    
if __name__ == "__main__":
    main()