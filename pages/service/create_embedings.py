from gensim.models import Word2Vec
from gensim.utils import simple_preprocess
from pinecone import Pinecone, ServerlessSpec
import os
from pdfminer.high_level import extract_text
from bs4 import BeautifulSoup
import numpy as np
import re

class CreateEmbeddings:
    def __init__(self):
        api_key = os.getenv('PINECONE_API_KEY')
        self.pc = Pinecone(api_key='a8861bb3-e7fa-469d-aecf-0372fbed64ee')
        # self.model = Word2Vec([["dummy"]],vector_size=384, min_count=1)
        self.model = Word2Vec.load('../model/semantic-search_word2vec4.model')
        self.index_name = 'callprep-case-studies'
        existing_indexes = self.pc.list_indexes()
        print(f"Existing indexes: {existing_indexes}")
        existing_index_names = [index['name'] for index in existing_indexes.indexes]
        print(f"Existing indexes: {existing_index_names}")
        if self.index_name not in existing_index_names:
            self.pc.create_index(
                self.index_name, 
                dimension=284,
                spec=ServerlessSpec(
                    cloud='aws', 
                    region='us-east-1'
                )
            )
        self.index = self.pc.Index(self.index_name)

    @staticmethod
    def clean_filename(filename):
        # Replace non-ASCII characters with a hyphen
        return re.sub(r'[^\x00-\x7F]+', '-', filename)
    
    def preprocess_text(self, doc_path):
        try:
            file_extension = os.path.splitext(doc_path)[1]
            if file_extension == '.pdf':
                text = extract_text(doc_path)
            elif file_extension == '.txt':
                with open(doc_path, 'r') as f:
                    text = f.read()
            elif file_extension == '.html':
                with open(doc_path, 'r') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    text = soup.get_text()
            else:
                print(f"Unsupported file type {file_extension}")
                return ""
            return text
        except Exception as e:
            print(f"Error extracting text from {doc_path}: {e}")
            return ""

    def create_and_save_embeddings(self, doc_path, file_name):
        file_name = self.clean_filename(file_name)
        text = self.preprocess_text(doc_path)
        if text:
            tokenized_text = simple_preprocess(text)
            self.model.build_vocab([tokenized_text], update=True)
            self.model.train([tokenized_text], total_examples=self.model.corpus_count, epochs=self.model.epochs)
            embedding = np.mean([self.model.wv[word] for word in tokenized_text if word in self.model.wv], axis=0)
            if np.all(np.isnan(embedding)):
                print(f"No words in {file_name} are in the model's vocabulary. Skipping this file.")
                return False
            embedding = embedding.tolist()            
            pinecone_metadata = {'filename': file_name}
            self.index.upsert([(file_name, embedding, pinecone_metadata)])
            return True
        else:
            return False
        
    def search_documents(self, query):
        words = simple_preprocess(query)
        word_vectors = [self.model.wv[word] for word in words if word in self.model.wv]
        if not word_vectors:
            print(f"No words in query '{query}' are in the model's vocabulary. Returning empty results.")
            return {'matches': []}
        query_embedding = np.mean(word_vectors, axis=0).tolist()
        results = self.index.query(vector=query_embedding, top_k=10)
        return results
create_embeddings = CreateEmbeddings()