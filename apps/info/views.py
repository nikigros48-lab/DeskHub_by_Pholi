from django.shortcuts import render

def main_page(request):
    return render(request, "info/main_page.html")

def about(request):
    return render(request, 'info/about.html')

def contacts(request):
    return render(request, 'info/contacts.html')