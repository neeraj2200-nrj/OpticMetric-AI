from django.db import models

class Patient(models.Model):
    patient_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} ({self.patient_id})"

class Analysis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='analyses')
    uploaded_image = models.ImageField(upload_to='uploads/')
    
    # ML Outputs
    disc_mask = models.ImageField(upload_to='results/disc/', blank=True, null=True)
    cup_mask = models.ImageField(upload_to='results/cup/', blank=True, null=True)
    overlay_image = models.ImageField(upload_to='results/overlay/', blank=True, null=True)
    
    # Extended ML Metrics
    disc_area = models.FloatField(blank=True, null=True)
    cup_area = models.FloatField(blank=True, null=True)
    rim_area = models.FloatField(blank=True, null=True)
    
    disc_height = models.IntegerField(blank=True, null=True)
    cup_height = models.IntegerField(blank=True, null=True)
    disc_width = models.IntegerField(blank=True, null=True)
    cup_width = models.IntegerField(blank=True, null=True)
    
    vcdr = models.FloatField(blank=True, null=True)
    hcdr = models.FloatField(blank=True, null=True)
    cdar = models.FloatField(blank=True, null=True)
    rim_ratio = models.FloatField(blank=True, null=True)
    
    diagnosis = models.CharField(max_length=100, default='Pending')
    confidence = models.FloatField(blank=True, null=True)
    
    # Intermediate ML Artifacts
    preprocessed_image = models.ImageField(upload_to='results/preprocessed/', blank=True, null=True)
    disc_prob_map = models.FileField(upload_to='results/prob_maps/', blank=True, null=True)
    cup_prob_map = models.FileField(upload_to='results/prob_maps/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.id} for {self.patient.name}"
