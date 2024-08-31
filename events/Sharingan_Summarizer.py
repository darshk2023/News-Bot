import requests
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
from transformers import pipeline
from rouge_score import rouge_scorer


class Sharingan_Summarizer:
    def __init__(self, sources, css_selectors):
        source_articles = {}
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.output_file = f"{current_date}_news.txt"
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)
        with open(self.output_file, 'w') as file:
            for source, css_selector in zip(sources, css_selectors):
                source_articles[source] = self.get_source_top_articles(source, css_selector)
            for source in source_articles:
                file.write("\n" + "*"*100 + "\n")
                file.write(f"Source: {source}")
                file.write("\n" + "*"*100 + "\n")
                file.write("\n" + "="*100 + "\n")
                for title, url in source_articles[source]:
                    file.write(f"Title: {title}\n")
                    file.write(f"URL: {url}\n")
                    article_text = self.extract_article_text(url)
                    summary = self.summarize(article_text)
                    file.write(f"Summary: {summary}")
                    file.write("\n" + "="*100 + "\n")
    def get_source_top_articles(self, source, css_selector):
        '''
        1) Fetch the HTML of news source's homepage.
        2) Parse the HTML content using BeautifulSoup.
        3) Extract the Data using CSS selectors to find and extract the titles and URLs of the top articles from source's home page.
        4) Return the the extracted information as a list of tuples.

        Input:
        - source: source's homepage link in string format.
        - css_selector: corresponding css_selector

        Output:
        - three_articles: list of at most 3 tuples of form (article_title, article_link).
        '''
        # Prepare source's html
        response = requests.get(source)
        soup = BeautifulSoup(response.content, "html.parser")
        # Find headline elements
        articles = []
        elements = soup.select(css_selector)
        # Find top 3 article title and corresponding links
        for item in elements:
            title = item.get_text().strip()
            link_element = item.find_parent("a")
            if not link_element:
                link_element = item.find("a")
            if link_element:
                link = link_element["href"]
                if link.startswith("/"):
                    link = source[0:(len(source)-1)] + link
                articles.append((title, link))
            if len(articles) == 3:
                break        
        return articles
    def extract_article_text(self, url):
        '''
        Using the Article class from newspaper, create an article object using a given URL.
        Then, downloads article's content and parses it to retrieve, clean, and return the text.

        Input:
            - url: URL of desired article in string format.

        Output:
            - article_text: extracted text from the article the URL pointed to.
        '''
        article = Article(url)
        article.download()
        article.parse()
        cleaned_text = (article.text).replace('\n', ' ').strip()
        return cleaned_text
    def chunk_text(self, text, max_length):
        '''
        Splits the text inot chunks of specified maximum length.

        Inputs:
            - text: extracted text from an article.
            - max_length: max word limit for bard-large-cnn LLM to process.

        Ouputs:
            - chunk: strings, each containining max_length # of words.
        '''
        words = text.split()
        for i in range(0, len(words), max_length):
            yield ' '.join(words[i:i+max_length])
    def summarize(self, text):
        '''
        Using HuggingFace's pipeline class in the transfomers library, the "facebook/bart-large-cnn" 
        model generated summaries based on the size of our text.

        Input:
            - text: extracted text from webscraped article

        Ouput:
            - summary: LLM generated summary of text
        '''
        max_input_length = 512 # Specific to the summarizer model used
        summaries = []
        for chunk in self.chunk_text(text, max_input_length):
            if len(chunk.split()) > 50:
                max_summary_length = len(chunk.split()) // 2 # Adjusted based on chunk size
                min_summary_length = max_summary_length // 5 # Adjusted based on chunk size
                summary = self.summarizer(chunk, min_length=min_summary_length, max_length=max_summary_length, do_sample=False)
                summaries.append(summary[0]['summary_text'])
        summary = ' '.join(summaries)
        sentences = summary.split(".")
        summary = '. '.join(sentences[:len(sentences) - 1])
        summary += "."
        return summary
    def calculate_rouge_scores(self, reference_text, candidate_text):
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(reference_text, candidate_text)
        return scores
    def get_save_path(self):
        return self.output_file
    
'''
EXAMPLE USAGE:

sources = [
    "https://www.cnn.com/",
    "https://www.foxnews.com/",
    "https://www.nbcnews.com/"
]
css_selectors = [
    ".container__headline-text",  # Updated selector: targets the headline titles
    ".title",
    ".multistoryline__headline"
]
tomoe_summarizer = Sharingan_Summarizer(sources, css_selectors)
'''
