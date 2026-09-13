from django.shortcuts import render, get_object_or_404, redirect
from analysis.models import Analysis
from ml.report_generation.clinical_report import interpret_vcdr

def clinical_report(request, analysis_id):
    """
    Renders the printable clinical report sheet for a specific scan.
    """
    analysis = get_object_or_404(Analysis, id=analysis_id)
    
    clf_system_results = None
    if analysis.vcdr is not None:
        features_list = [
            analysis.disc_area,
            analysis.cup_area,
            analysis.rim_area,
            analysis.disc_height,
            analysis.cup_height,
            analysis.disc_width,
            analysis.cup_width,
            analysis.vcdr,
            analysis.hcdr,
            analysis.cdar,
            analysis.rim_ratio
        ]
        from ml.classification.classifier import classify_features_all
        try:
            clf_system_results = classify_features_all(features_list)
        except Exception as e:
            print(f"Error classifying in clinical_report: {e}")

    interpretation = "Pending Pipeline Execution"
    recommendations = "Pending clinical pipeline execution."
    if analysis.vcdr is not None:
        interpretation, recommendations = interpret_vcdr(analysis.vcdr)
            
    context = {
        'analysis': analysis,
        'is_completed': analysis.vcdr is not None,
        'clf_results': clf_system_results,
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
