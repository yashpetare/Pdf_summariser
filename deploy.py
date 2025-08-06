
#!/usr/bin/env python3

import os
import nltk
import pytesseract
import re
import slate3k as slate
from pdf2image import convert_from_path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.snowball import SnowballStemmer
from PIL import Image
import streamlit as st

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

def extract_text(file):
    with open(file, "rb") as pdf_file_obj:
        pdf_pages = slate.PDF(pdf_file_obj)

        # Extract text from PDF file
        text = ""
        for page in pdf_pages:
            text += page
        return text

def extract_ocr(file):
    pages = convert_from_path(file, 500)

    image_counter = 1
    for page in pages:
        filename = "page_" + str(image_counter) + ".jpg"
        page.save(filename, "JPEG")
        image_counter += 1

    limit = image_counter - 1
    text = ""
    for i in range(1, limit + 1):
        filename = "page_" + str(i) + ".jpg"
        page = str(((pytesseract.image_to_string(Image.open(filename)))))
        page = page.replace("-\n", "")
        text += page
        os.remove(filename)
    return text

def summarize(text):
    # Process text by removing numbers and unrecognized punctuation
    processed_text = re.sub("’", "'", text)
    processed_text = re.sub("[^a-zA-Z' ]+", " ", processed_text)
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(processed_text)

    # Normalize words with Porter stemming and build word frequency table
    stemmer = SnowballStemmer("english", ignore_stopwords=True)
    freq_table = dict()
    for word in words:
        word = word.lower()
        if word in stop_words:
            continue
        stemmed_word = stemmer.stem(word)
        if stemmed_word in freq_table:
            freq_table[stemmed_word] += 1
        else:
            freq_table[stemmed_word] = 1

    # Normalize every sentence in the text
    sentences = sent_tokenize(text)
    sentence_value = dict()
    for sentence in sentences:
        sentence_value[sentence] = 0
        for word in word_tokenize(sentence.lower()):
            stemmed_word = stemmer.stem(word)
            if stemmed_word in freq_table:
                sentence_value[sentence] += freq_table[stemmed_word]

    # Determine average value of a sentence in the text
    sum_values = sum(sentence_value.values())
    average = int(sum_values / len(sentence_value))

    # Create summary of text using sentences that exceed the average value by some factor
    summary = ""
    for sentence in sentences:
        if sentence_value[sentence] > (3.0 * average):
            summary += " " + sentence

    return summary

# Streamlit Interface
st.title("PDF Summarizer")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    option = st.radio("Choose extraction method", ("Direct Text Extraction", "OCR Extraction"))

    if st.button("Summarize PDF"):
        if option == "Direct Text Extraction":
            text = extract_text(uploaded_file)
        elif option == "OCR Extraction":
            text = extract_ocr(uploaded_file)
        else:
            st.error("Invalid option selected!")
            text = None

        if text:
            summary = summarize(text)
            st.subheader("Summary")
            st.write(summary)
