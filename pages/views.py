from django.shortcuts import render
from django.conf import settings
import os

# Create your views here.
def home(request):
    return render(request, "pages/home.html", {})

def search(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        return render(request, "pages/searchresult.html", {})
    
    return render(request, "pages/search.html", {})

def upload(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('file') 
        for f in uploaded_files:
            # Define the path to save the file. This example saves files to MEDIA_ROOT/uploads
            file_path = os.path.join(settings.MEDIA_ROOT, 'UplodedDocs', f.name)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # Open the file path for writing in binary mode and save the file
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
        return render(request, "pages/upload.html", {'message': 'Files successfully uploaded'})
    
    return render(request, "pages/upload.html", {})
