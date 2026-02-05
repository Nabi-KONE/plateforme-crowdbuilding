from django import forms
from .models import ParametreNotification

class ParametreNotificationForm(forms.ModelForm):
    class Meta:
        model = ParametreNotification
        fields = [
            'email_projet_valide',
            'email_nouvel_investissement', 
            'email_objectif_atteint',
            'email_nouveau_commentaire',
            'email_mise_a_jour',
            'resume_quotidien',
            'resume_hebdomadaire',
        ]
        widgets = {
            'email_projet_valide': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_nouvel_investissement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_objectif_atteint': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_nouveau_commentaire': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_mise_a_jour': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resume_quotidien': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resume_hebdomadaire': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }