from django.shortcuts import render
from django.conf import settings
from pages.service.EmbeddingsHandler import EmbeddingsHandler
import os
import threading

embeddingsHandler = EmbeddingsHandler()

# Create your views here.
def home(request):
    return render(request, "pages/home.html", {})

def search(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        print(f"Query received: {query}")
        result=embeddingsHandler.search_documents(query)
        print("search result :: ",result)
        return render(request, "pages/searchresult.html", {'results': result['matches']})
    
    return render(request, "pages/search.html", {})

def create_embeddings_in_background(uploaded_files, file_dir):
    failed_files = []
    for f in uploaded_files:
        file_path = os.path.join(file_dir, f.name)
        try:
            embeddingsHandler.create_and_save_embeddings(file_path, f.name)
        except Exception as e:
            failed_files.append(f.name)
            print(f"Error creating embeddings for {f.name}: {e}")
            try:
                os.remove(file_path)
                print(f"Removed failed file: {f.name}")
            except Exception as remove_error:
                print(f"Error removing file {f.name}: {remove_error}")
    return failed_files 

def upload(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('file') 
        for f in uploaded_files:
            # Define the path to save the file. This example saves files to MEDIA_ROOT/uploads
            file_path = os.path.join(settings.MEDIA_ROOT, 'UplodedDocs', f.name)
            file_dir = os.path.join(settings.MEDIA_ROOT, 'UplodedDocs')
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # Open the file path for writing in binary mode and save the file
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
        
        # threading.Thread(target=create_embeddings_in_background, args=(uploaded_files, file_dir)).start()
        failed_files = create_embeddings_in_background(uploaded_files, file_dir)
        if failed_files:
            message = 'Failed to create embeddings for the following files:'
        else:
            message = 'All files processed successfully.'
        return render(request, "pages/upload.html", {'message': message, 'failed_files': failed_files, "status": "complete"})
    
    return render(request, "pages/upload.html")
