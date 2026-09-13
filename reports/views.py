from django.shortcuts import render, get_object_or_404, redirect
from analysis.models import Analysis
from ml.report_generation.clinical_report import interpret_vcdr

def clinical_report(request, analysis_id):
    """
    Renders the printable clinical report sheet for a specific scan.
    """
    analysis = get_object_or_404(Analysis, id=analysis_id)
    
    interpretation = "Pending Pipeline Execution"
    recommendations = "Pending clinical pipeline execution."
    if analysis.vcdr is not None:
        interpretation, recommendations = interpret_vcdr(analysis.vcdr)
            
    context = {
        'analysis': analysis,
        'is_completed': analysis.vcdr is not None,
        'interpretation': interpretation,
        'recommendations': recommendations,
    }
    return render(request, 'reports/report.html', context)

def clinical_report_default(request):
    """
    Handles sidebar redirect: routes to the most recent analysis record.
    If database is empty, creates a dummy temporary state.
    """
    latest = Analysis.objects.all().order_by('-created_at').first()
    if latest:
        return redirect('reports:clinical_report', analysis_id=latest.id)
    
    # If no analyses exist, render a template requesting upload, or direct to dashboard
    return render(request, 'reports/report.html', {'analysis': None, 'is_completed': False})
