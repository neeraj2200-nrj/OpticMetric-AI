from django.db import models

class Clinician(models.Model):
    name = models.CharField(max_length=100, default="Dr. Sarah Jenkins")
    facility_name = models.CharField(max_length=150, default="St. Jude Medical Center")
    department_name = models.CharField(max_length=150, default="Ophthalmology Department")
    lab_details = models.CharField(max_length=150, default="Clinical Analysis Lab #4-B")
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    @property
    def initials(self):
        """
        Extracts the first letter of the clinician's actual name,
        intelligently bypassing prefixes like Dr., Mr., Ms., Prof.
        """
        if self.name:
            stripped = self.name.strip()
            parts = stripped.split()
            if len(parts) > 1 and parts[0].lower() in ['dr', 'dr.', 'mr', 'mr.', 'ms', 'ms.', 'prof', 'prof.']:
                return parts[1][0].upper()
            return stripped[0].upper()
        return "U"

    def __str__(self):
        return self.name
