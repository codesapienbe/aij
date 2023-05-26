import requests
from bs4 import BeautifulSoup
import re

# define a function to extract text from a webpage
def extract_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    text = ""
    for p in soup.find_all("p"):
        text += p.get_text()
    return text

# preprocess the data
def preprocess(text):
    # remove URLs
    text = re.sub(r"http\S+", "", text)
    # remove special characters and digits
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    # convert to lowercase
    text = text.lower()
    return text


def main():
    
    # collect data from news websites
    news_urls = [
        "https://www.nytimes.com/",
        "https://www.washingtonpost.com/",
        "https://www.bbc.com/news",
    ]
    news_text = []
    for url in news_urls:
        news_text.append(extract_text(url))
        
        
    # collect data from social media platforms
    social_media_urls = [
        "https://www.twitter.com/",
        "https://www.facebook.com/",
        "https://www.instagram.com/",
    ]
    social_media_text = []
    for url in social_media_urls:
        social_media_text.append(extract_text(url))
        
        
    # collect data from blogs
    blog_urls = [
        "https://www.medium.com/",
        "https://www.wordpress.com/",
        "https://www.blogger.com/",
    ]
    blog_text = []
    for url in blog_urls:
        blog_text.append(extract_text(url))
    
    news_text = [preprocess(text) for text in news_text]
    social_media_text = [preprocess(text) for text in social_media_text]
    blog_text = [preprocess(text) for text in blog_text]

    # combine the datasets
    training_data = news_text + social_media_text + blog_text
    
    print(training_data)