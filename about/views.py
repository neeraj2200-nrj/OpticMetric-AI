from django.shortcuts import render

def about_methodology(request):
    """
    Renders the scientific methodology, neural architectures, and data flowchart of the workstation.
    """
    return render(request, 'about/about.html')
