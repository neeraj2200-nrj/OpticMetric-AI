import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from analysis.models import Patient, Analysis
from ml.inference import run_inference

class Command(BaseCommand):
    help = "Seeds the database with clinical sample patient records and REFUGE-style scans."

    def handle(self, *args, **options):
        self.stdout.write("Starting data seeding process...")

        # Flashing existing patient and analysis tables to prevent duplicates
        self.stdout.write("Flushing existing patient and analysis tables...")
        Analysis.objects.all().delete()
        Patient.objects.all().delete()

        # Seed Patients definitions
        patients_data = [
            {'id': 'REF-V0095', 'name': 'Sample 001', 'age': 65, 'gender': 'Male'},
            {'id': 'REF-V0125', 'name': 'Sample 002', 'age': 58, 'gender': 'Female'},
            {'id': 'REF-V0096', 'name': 'Sample 003', 'age': 71, 'gender': 'Male'},
            {'id': 'REF-V0126', 'name': 'Sample 004', 'age': 62, 'gender': 'Female'}
        ]

        patients = {}
        for p in patients_data:
            patient = Patient.objects.create(
                patient_id=p['id'],
                name=p['name'],
                age=p['age'],
                gender=p['gender']
            )
            patients[p['id']] = patient
            self.stdout.write(f"Created Patient record: {patient}")

        # Seed Analysis records
        analyses_data = [
            {
                'patient_id': 'REF-V0095',
                'filename': 'V0006.jpg',
            },
            {
                'patient_id': 'REF-V0125',
                'filename': 'V0041.jpg',
            },
            {
                'patient_id': 'REF-V0096',
                'filename': 'V0006.jpg', # Reuse local file V0006.jpg
            },
            {
                'patient_id': 'REF-V0126',
                'filename': 'V0041.jpg', # Reuse local file V0041.jpg
            }
        ]

        for a in analyses_data:
            patient = patients[a['patient_id']]
            filename = a['filename']
            local_image_path = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)
            
            # Check if sample image exists locally
            if os.path.exists(local_image_path):
                self.stdout.write(f"Local image found: {filename}. Running pipeline inference...")
                
                # Run actual ML inference pipeline on local asset
                results = run_inference(local_image_path)
                
                if results.get('error') is None:
                    analysis = Analysis.objects.create(
                        patient=patient,
                        uploaded_image=f"uploads/{filename}",
                        disc_mask=results['disc_mask'],
                        cup_mask=results['cup_mask'],
                        overlay_image=results['overlay_image'],
                        preprocessed_image=results['preprocessed_image'],
                        disc_prob_map=results['disc_prob_map'],
                        cup_prob_map=results['cup_prob_map'],
                        disc_area=results['disc_area'],
                        cup_area=results['cup_area'],
                        rim_area=results['rim_area'],
                        disc_height=results['disc_height'],
                        cup_height=results['cup_height'],
                        disc_width=results['disc_width'],
                        cup_width=results['cup_width'],
                        vcdr=results['vcdr'],
                        hcdr=results['hcdr'],
                        cdar=results['cdar'],
                        rim_ratio=results['rim_ratio'],
                        diagnosis=results['diagnosis'],
                        confidence=results['confidence'],
                        created_at=timezone.now()
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created real Analysis for {patient.patient_id} with VCDR {results['vcdr']:.3f}"))
                else:
                    self.stdout.write(self.style.WARNING(f"ML Pipeline error during seeding for {filename}: {results['error']}"))
                    # Fallback to empty/pending record
                    analysis = Analysis.objects.create(
                        patient=patient,
                        uploaded_image=f"uploads/{filename}",
                        created_at=timezone.now()
                    )
            else:
                self.stdout.write(f"Local image NOT found: {filename}. Skipping inference step.")
                # Create empty/pending Analysis record
                analysis = Analysis.objects.create(
                    patient=patient,
                    uploaded_image=f"uploads/{filename}",
                    created_at=timezone.now()
                )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully."))
