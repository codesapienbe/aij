from transformers import pipeline

def sentiment_analysis(text):

    # load the sentiment analysis model
    classifier = pipeline("sentiment-analysis")

    # apply sentiment analysis
    result = classifier(text)
    
    return result


def main():
    
    # sample text
    text = "I love this new phone, it's amazing!"
    
    result = sentiment_analysis(text)

    # print the results
    print("Original text:", text)
    print("Sentiment analysis result:", result)
    
    
if __name__ == "__main__":
    main()