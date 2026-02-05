"""
Formulaires pour la gestion des documents
Plateforme crowdBuilding - Burkina Faso
"""
from django import forms
from .models import Document, TypeDocument


class UploadDocumentForm(forms.ModelForm):
    """Formulaire pour uploader un document"""
    
    class Meta:
        model = Document
        fields = ['nom', 'type', 'fichier']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: CNI, Relevé bancaire, Statuts entreprise...'
            }),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nom du document',
            'type': 'Type de document',
            'fichier': 'Fichier à uploader',
        }
    
    def __init__(self, *args, **kwargs):
        self.utilisateur = kwargs.pop('utilisateur', None)
        super().__init__(*args, **kwargs)
        
        # Adapter les types de documents selon le rôle de l'utilisateur
        if self.utilisateur and hasattr(self.utilisateur, 'get_role_actif'):
            role_actif = self.utilisateur.get_role_actif()
            if role_actif:
                role_type = role_actif.type
                
                if role_type == 'INVESTISSEUR':
                    self.fields['type'].choices = [
                        ('', 'Sélectionnez le type de document'),
                        (TypeDocument.JUSTIFICATIF_IDENTITE, 'Justificatif d\'identité (CNI, Passeport)'),
                        (TypeDocument.JUSTIFICATIF_REVENU, 'Justificatif de revenus'),
                        (TypeDocument.JUSTIFICATIF_FONDS, 'Justificatif d\'origine des fonds'),
                    ]
                elif role_type == 'PROMOTEUR':
                    self.fields['type'].choices = [
                        ('', 'Sélectionnez le type de document'),
                        (TypeDocument.JUSTIFICATIF_IDENTITE, 'Justificatif d\'identité'),
                        (TypeDocument.JUSTIFICATIF_REVENU, 'Justificatif de revenus'),
                        (TypeDocument.STATUTS_ENTREPRISE, 'Statuts d\'entreprise'),
                        (TypeDocument.PLAN_FINANCIER, 'Plan financier'),
                        (TypeDocument.DOCUMENT_PROJET, 'Document de projet'),
                    ]
    
    def clean_fichier(self):
        """Validation du fichier"""
        fichier = self.cleaned_data.get('fichier')
        
        if fichier:
            # Vérifier la taille (max 10MB)
            if fichier.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Le fichier est trop volumineux. Taille maximale: 10MB.')
            
            # Vérifier l'extension
            extensions_autorisees = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            import os
            extension = os.path.splitext(fichier.name)[1].lower()
            if extension not in extensions_autorisees:
                raise forms.ValidationError(
                    f'Format de fichier non autorisé. Formats acceptés: {", ".join(extensions_autorisees)}'
                )
        
        return fichier