from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Board


def home(request):
    return render(request, 'home.html', {'boards': Board.objects.all()})

def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    return render(request, 'topics.html', {'board': board})
