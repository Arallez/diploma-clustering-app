import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .algorithms import (
    kmeans_step, 
    dbscan_step, 
    forel_step, 
    agglomerative_step,
    compute_dendrogram_data,
    mean_shift_step
)
from .presets import generate_preset

# --- Page Views ---

def index(request):
    """Main simulator page"""
    return render(request, 'simulator/index.html')

def task_list(request):
    """List of educational tasks (Placeholder restored)"""
    # In a real app, this would fetch tasks from DB
    return render(request, 'simulator/task_list.html', {'tasks': []})

def challenge_detail(request, slug):
    """Specific challenge page (Placeholder restored)"""
    return render(request, 'simulator/challenge_detail.html', {'slug': slug})

# --- API Endpoints ---

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
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs to satisfy old urls.py until we update it
@csrf_exempt
def get_preset(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        n_samples = int(request.GET.get('samples', 100))
        try:
            points = generate_preset(name, n_samples)
            return JsonResponse({'success': True, 'points': points})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def get_dendrogram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            
            dendro_data = compute_dendrogram_data(points)
            
            return JsonResponse({
                'success': True, 
                'dendrogram': {
                    'icoord': dendro_data['icoord'],
                    'dcoord': dendro_data['dcoord'],
                    'ivl': dendro_data['ivl'],
                    'leaves': dendro_data['leaves']
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def run_kmeans(request): return run_algorithm(request)
@csrf_exempt
def run_dbscan(request): return run_algorithm(request)
@csrf_exempt
def run_forel(request): return run_algorithm(request)
@csrf_exempt
def run_agglomerative(request): return run_algorithm(request)
@csrf_exempt
def check_solution(request): return JsonResponse({'success': False, 'error': 'Not implemented'})
