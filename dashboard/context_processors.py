from .models import Clinician

def clinician_context(request):
    """
    Ensures the clinician profile database instance is loaded and
    available globally inside all template contexts.
    """
    clinician, created = Clinician.objects.get_or_create(id=1)
    return {'clinician': clinician}
