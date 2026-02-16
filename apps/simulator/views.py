import json
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .algorithms import (
    kmeans_step,
    dbscan_step,
    forel_step,
    agglomerative_step,
    mean_shift_step,
    compute_dendrogram_data,
)
from .presets import generate_preset


@ensure_csrf_cookie
def index(request):
    """Страница симулятора (песочница: точки + алгоритмы)."""
    return render(request, 'simulator/index.html')


def _redirect_legacy_challenge(request, slug):
    """Редирект со старого /simulator/challenge/<slug>/ на /tasks/challenge/<slug>/."""
    return redirect(reverse('tasks:challenge_detail', kwargs={'slug': slug}), permanent=False)


# --- API Endpoints ---

@csrf_exempt
def get_preset(request):
    """
    Returns points for a selected preset (Blobs, Moons, etc.)
    """
    if request.method == 'GET':
        try:
            # Get params (frontend sends 'name', keeping 'preset' for backward compat)
            preset_name = request.GET.get('name') or request.GET.get('preset') or 'blobs'
            
            # Generate 300 points by default for the simulator
            data = generate_preset(preset_name, n_samples=300)
            
            return JsonResponse({'success': True, 'points': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def run_algorithm(request):
    """Unified endpoint for running all clustering algorithms"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            algo = data.get('algorithm')
            points = data.get('points', [])
            params = data.get('params', {})
            
            history = []
            
            if algo == 'kmeans':
                k = int(params.get('k', 3))
                history = kmeans_step(points, k)
            elif algo == 'dbscan':
                eps = float(params.get('eps', 0.5))
                min_pts = int(params.get('minPts', 3))
                history = dbscan_step(points, eps, min_pts)
            elif algo == 'forel':
                r = float(params.get('radius', 1.0))
                history = forel_step(points, r)
            elif algo == 'agglomerative':
                k = int(params.get('k', 2))
                history = agglomerative_step(points, k)
            elif algo == 'meanshift':
                bandwidth = float(params.get('bandwidth', 1.0))
                history = mean_shift_step(points, bandwidth)
            else:
                return JsonResponse({'success': False, 'error': f'Unknown algorithm: {algo}'})
                
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def get_dendrogram(request):
    """
    Returns dendrogram data for plotting.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            
            ddata = compute_dendrogram_data(points)
            
            if 'error' in ddata:
                return JsonResponse({'success': False, 'error': ddata['error']})
            
            return JsonResponse({'success': True, 'dendrogram': ddata})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs
@csrf_exempt
def run_kmeans(request): return run_algorithm(request)
@csrf_exempt
def run_dbscan(request): return run_algorithm(request)
@csrf_exempt
def run_forel(request): return run_algorithm(request)
@csrf_exempt
def run_agglomerative(request): return run_algorithm(request)
