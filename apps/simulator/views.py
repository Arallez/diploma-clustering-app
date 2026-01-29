import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .algorithms import (
    kmeans_step, 
    dbscan_step, 
    forel_step, 
    agglomerative_step,
    compute_dendrogram_data,
    mean_shift_step
)
from .presets import generate_preset

def index(request):
    return render(request, 'simulator/index.html')

@csrf_exempt
def run_algorithm(request):
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
                return JsonResponse({'success': False, 'error': 'Unknown algorithm'})
                
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

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
