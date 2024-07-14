from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os
from pdfminer.high_level import extract_text
import numpy as np
import re
from fuzzywuzzy import process


class EmbeddingsHandler:
    def __init__(self):
        api_key = os.getenv('PINECONE_API_KEY')
        self.pc = Pinecone(api_key='a8861bb3-e7fa-469d-aecf-0372fbed64ee')
        self.model = SentenceTransformer('pages/model/modelst/semantic-search_ST_1.model')

        self.index_name = 'gail-archives'
        existing_indexes = self.pc.list_indexes()
        # print(f"Existing indexes: {existing_indexes}")
        existing_index_names = [index['name'] for index in existing_indexes.indexes]
        print(f"Existing indexes: {existing_index_names}")
        if self.index_name not in existing_index_names:
            self.pc.create_index(
                self.index_name, 
                dimension=384,
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
            if file_extension == '.pdf' or file_extension == '.PDF':
                text = extract_text(doc_path)
            elif file_extension == '.txt' or file_extension == '.TXT':
                with open(doc_path, 'r') as f:
                    text = f.read()
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
            text_embedding = self.model.encode(text)
            filename_embedding = self.model.encode(file_name)
            if np.all(np.isnan(text_embedding))  and np.all(np.isnan(filename_embedding)):
                print(f"No words in {file_name} are in the model's vocabulary. Skipping this file.")
                return False
            combined_embedding = (text_embedding + 2 * filename_embedding) / 3

            if not np.all(np.isnan(combined_embedding)):
                combined_embedding = combined_embedding.tolist()            
                pinecone_metadata = {'filename': file_name}
                self.index.upsert([(file_name, combined_embedding, pinecone_metadata)])
                return True
            else:
                print(f"Combined embedding for {file_name} resulted in NaN. Skipping this file.")
                return False
        else:
            return False

    def search_documents(self, query):
        query_embedding = self.model.encode([query])[0]
        search_results = self.index.query(vector=query_embedding.tolist(), top_k=50)

        # query_words = set(query.lower().split())
        # for match in search_results['matches']:
        #     doc_id_words = set(match['id'].lower().replace('.pdf', '').replace('_', ' ').replace('-', ' ').split())
        #     match['word_matches'] = 0
        #     for query_word in query_words:
        #         best_match, similarity = process.extractOne(query_word, doc_id_words)
        #         if similarity >= 80:
        #             match['word_matches'] += 1

        # sorted_results = sorted(search_results['matches'], key=lambda x: (-x['word_matches'], -x['score']))
        # search_results['matches'] = sorted_results

        return search_results
    
# embeddingsHandler = EmbeddingsHandler()