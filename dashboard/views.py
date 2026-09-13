import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from analysis.models import Analysis
from .models import Clinician

def dashboard_home(request):
    """
    Renders the clinical workstation dashboard, computing metrics and listing recent scans,
    supporting filtering (by diagnosis and gender) and sorting options dynamically.
    """
    analyses = Analysis.objects.all()
    
    # 1. Capture dynamic filters from GET parameters
    diag = request.GET.get('diag', 'all')
    gender = request.GET.get('gender', 'all')
    sort = request.GET.get('sort', 'newest')
    
    # 2. Apply filters
    if diag == 'glaucoma':
        analyses = analyses.filter(diagnosis='Glaucoma')
    elif diag == 'normal':
        analyses = analyses.filter(diagnosis='Normal')
    elif diag == 'pending':
        analyses = analyses.filter(vcdr__isnull=True)
        
    if gender in ['Male', 'Female']:
        analyses = analyses.filter(patient__gender=gender)
        
    # 3. Apply sorting
    if sort == 'confidence_high':
        analyses = analyses.order_by('-confidence')
    elif sort == 'confidence_low':
        analyses = analyses.order_by('confidence')
    elif sort == 'vcdr_high':
        analyses = analyses.order_by('-vcdr')
    else: # newest
        analyses = analyses.order_by('-created_at')
        
    # Compute clinical metrics counts from base query (unfiltered for accurate stats cards)
    base_analyses = Analysis.objects.all()
    total_scans = base_analyses.count()
    suspects_count = base_analyses.filter(diagnosis='Glaucoma').count()
    normal_count = base_analyses.filter(diagnosis='Normal').count()
    pending_count = base_analyses.filter(vcdr__isnull=True).count()
    
    # Average speed / latency
    avg_processing_speed = 1.4 # seconds

    # Dynamic Workstation Scan Activity Calculation from Real Database Timestamps
    from django.db.models.functions import TruncDate, TruncHour
    from django.db.models import Count

    activity_data = []
    if total_scans > 0:
        # Try hourly grouping first
        hourly_counts = list(base_analyses.annotate(hour=TruncHour('created_at')).values('hour').annotate(count=Count('id')).order_by('hour'))
        if len(hourly_counts) >= 3:
            max_c = max([item['count'] for item in hourly_counts]) or 1
            for item in hourly_counts[-10:]:
                h_str = item['hour'].strftime('%H:%M') if item['hour'] else 'Scan'
                pct = int((item['count'] / max_c) * 100)
                activity_data.append({'label': h_str, 'count': item['count'], 'pct': max(pct, 12)})
        else:
            daily_counts = list(base_analyses.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date'))
            max_c = max([item['count'] for item in daily_counts]) or 1
            for item in daily_counts[-10:]:
                d_str = item['date'].strftime('%b %d') if item['date'] else 'Date'
                pct = int((item['count'] / max_c) * 100)
                activity_data.append({'label': d_str, 'count': item['count'], 'pct': max(pct, 12)})
    
    if not activity_data:
        activity_data = [
            {'label': '08:00 AM', 'count': 0, 'pct': 5},
            {'label': '12:00 PM', 'count': 0, 'pct': 5},
            {'label': '05:00 PM', 'count': 0, 'pct': 5}
        ]

    context = {
        'analyses': analyses[:10], # top 10 matching records
        'total_scans': total_scans,
        'suspects_count': suspects_count,
        'normal_count': normal_count,
        'pending_count': pending_count,
        'avg_processing_speed': avg_processing_speed,
        'activity_data': activity_data,
    }
    return render(request, 'dashboard/home.html', context)

def model_comparison(request):
    """
    Renders the Model Comparison view presenting authoritative benchmarks
    from the unseen REFUGE Validation400 dataset across 5 ML classifiers.
    """
    models_data = [
        {
            'name': 'Logistic Regression',
            'key': 'logistic_regression',
            'accuracy': 85.75,
            'precision': 39.76,
            'recall': 82.50,
            'specificity': 86.11,
            'f1': 53.66,
            'roc_auc': 93.77,
            'highlights': {'recall': True, 'roc_auc': True}
        },
        {
            'name': 'Support Vector Machine (SVM)',
            'key': 'svm',
            'accuracy': 92.25,
            'precision': 68.00,
            'recall': 42.50,
            'specificity': 97.78,
            'f1': 52.31,
            'roc_auc': 92.19,
            'highlights': {'accuracy': True, 'precision': True, 'specificity': True}
        },
        {
            'name': 'XGBoost',
            'key': 'xgboost',
            'accuracy': 91.50,
            'precision': 58.33,
            'recall': 52.50,
            'specificity': 95.83,
            'f1': 55.26,
            'roc_auc': 91.58,
            'highlights': {}
        },
        {
            'name': 'Multi-Layer Perceptron (MLP)',
            'key': 'mlp',
            'accuracy': 92.25,
            'precision': 63.64,
            'recall': 52.50,
            'specificity': 96.67,
            'f1': 57.53,
            'roc_auc': 89.67,
            'highlights': {'accuracy': True, 'f1': True}
        },
        {
            'name': 'Extra Trees',
            'key': 'extra_trees',
            'accuracy': 91.75,
            'precision': 59.46,
            'recall': 55.00,
            'specificity': 95.83,
            'f1': 57.14,
            'roc_auc': 88.65,
            'highlights': {}
        }
    ]
    
    context = {
        'models_data': models_data,
        'dataset_name': 'Unseen REFUGE Validation400 Dataset',
    }
    return render(request, 'dashboard/model_comparison.html', context)

def update_clinician(request):
    """
    Handles POST requests from Settings Modal to modify clinician name, facility details, and profile picture.
    """
    if request.method == 'POST':
        clinician, created = Clinician.objects.get_or_create(id=1)
        
        # 1. Update clinician name and facility details
        name = request.POST.get('name', '').strip()
        if name:
            clinician.name = name

        facility_name = request.POST.get('facility_name', '').strip()
        if facility_name:
            clinician.facility_name = facility_name

        department_name = request.POST.get('department_name', '').strip()
        if department_name:
            clinician.department_name = department_name

        lab_details = request.POST.get('lab_details', '').strip()
        if lab_details:
            clinician.lab_details = lab_details
            
        # 2. Handle profile picture deletion
        if request.POST.get('delete_picture') == 'true':
            if clinician.profile_picture:
                old_pic_path = clinician.profile_picture.path
                if os.path.exists(old_pic_path):
                    try:
                        os.remove(old_pic_path)
                    except Exception as e:
                        print(f"Failed to delete old profile picture file: {e}")
                clinician.profile_picture = None
                
        # 3. Handle new profile picture upload
        if request.FILES.get('profile_picture'):
            new_file = request.FILES['profile_picture']
            if clinician.profile_picture:
                old_pic_path = clinician.profile_picture.path
                if os.path.exists(old_pic_path):
                    try:
                        os.remove(old_pic_path)
                    except Exception as e:
                        print(f"Failed to delete old profile picture file: {e}")
            clinician.profile_picture = new_file
            
        clinician.save()
        messages.success(request, "Clinician profile and clinical facility settings updated successfully.")
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))

def coming_soon(request):
    """
    Renders the coming soon placeholder for future workstation expansions.
    """
    module_key = request.GET.get('module', 'generic')
    module_names = {
        'history': 'Patient History & Longitudinal Tracking',
        'batch': 'Batch Analysis & Processing Queue',
    }
    module_name = module_names.get(module_key, 'Requested Workspace Panel')
    
    context = {
        'module_key': module_key,
        'module_name': module_name,
    }
    return render(request, 'coming_soon.html', context)
