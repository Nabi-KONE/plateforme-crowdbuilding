"""
Formulaires pour la gestion des utilisateurs et des rôles
Plateforme crowdBuilding - Burkina Faso
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Utilisateur, Role, TypeRole


class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription personnalisé
    """
    TYPE_ROLE_CHOICES = [
        ('', 'Sélectionnez votre profil'),
        (TypeRole.INVESTISSEUR, 'Investisseur'),
        (TypeRole.PROMOTEUR, 'Promoteur'),
    ]
    
    prenom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        }),
        label='Prénom'
    )
    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        }),
        label='Nom'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        }),
        label='Email'
    )
    telephone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+226 XX XX XX XX'
        }),
        label='Téléphone (optionnel)'
    )
    profession = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre profession'
        }),
        label='Profession (optionnel)'
    )
    entreprise = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre entreprise'
        }),
        label='Entreprise (optionnel)'
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Décrivez votre expérience...'
        }),
        label='Expérience (optionnel)'
    )
    
    # CHANGER LE NOM DU CHAMP : type -> role_type
    role_type = forms.ChoiceField(  # <-- CHANGÉ: type -> role_type
        choices=TYPE_ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Type de compte'
    )
    
    conditions_acceptees = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='J\'accepte les conditions générales d\'utilisation'
    )
    
    class Meta:
        model = Utilisateur
        # ENLEVER 'type' car ce n'est pas un champ du modèle Utilisateur
        # AJOUTER les champs password1 et password2
        fields = ('prenom', 'nom', 'email', 'telephone', 'profession', 
                 'entreprise', 'experience', 'password1', 'password2', 
                 'conditions_acceptees')
        # Note: 'role_type' n'est pas dans fields car c'est un champ du formulaire, pas du modèle
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les champs de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmation du mot de passe'
        
        # Réorganiser l'ordre des champs si besoin
        field_order = ['prenom', 'nom', 'email', 'telephone', 'profession',
                      'entreprise', 'experience', 'role_type', 'password1',
                      'password2', 'conditions_acceptees']
        
        # Réordonner les champs
        self.fields = {key: self.fields[key] for key in field_order if key in self.fields}
    
    def clean_email(self):
        """Vérifier que l'email est unique"""
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError('Cet email est déjà utilisé.')
        return email
    
    def clean_telephone(self):
        """Valider le format du téléphone"""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Validation basique du format téléphone burkinabè
            import re
            if not re.match(r'^(\+226|226)?[0-9]{8}$', telephone.replace(' ', '')):
                raise forms.ValidationError('Format de téléphone invalide. Utilisez le format: +226 XX XX XX XX')
        return telephone
    
    def save(self, commit=True):
        """Sauvegarder l'utilisateur et créer son rôle"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.prenom = self.cleaned_data['prenom']
        user.nom = self.cleaned_data['nom']
        user.telephone = self.cleaned_data['telephone']
        user.profession = self.cleaned_data['profession']
        user.entreprise = self.cleaned_data['entreprise']
        user.experience = self.cleaned_data['experience']
        
        if commit:
            user.save()
            # Créer le rôle associé
            role_type = self.cleaned_data['role_type']  # <-- CHANGÉ: type -> role_type
            Role.objects.create(
                utilisateur=user,
                type=role_type,  # ICI: 'type' est le nom du champ dans le modèle Role
                statut='EN_ATTENTE_VALIDATION',
                role_actif=True
            )
        
        return user


class ConnexionForm(forms.Form):
    """
    Formulaire de connexion
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com',
            'autofocus': True
        }),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe'
        }),
        label='Mot de passe'
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Se souvenir de moi'
    )


class ProfilForm(forms.ModelForm):
    """
    Formulaire de modification du profil utilisateur
    """
    class Meta:
        model = Utilisateur
        fields = ['prenom', 'nom', 'telephone', 'profession', 'entreprise', 'experience']
        widgets = {
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'entreprise': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le téléphone optionnel
        self.fields['telephone'].required = False
        self.fields['profession'].required = False
        self.fields['entreprise'].required = False
        self.fields['experience'].required = False
    
    def clean_telephone(self):
        """Valider le format du téléphone"""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            import re
            if not re.match(r'^(\+226|226)?[0-9]{8}$', telephone.replace(' ', '')):
                raise ValidationError('Format de téléphone invalide. Utilisez le format: +226 XX XX XX XX')
        return telephone


class ChangementMotDePasseForm(forms.Form):
    """
    Formulaire de changement de mot de passe
    """
    ancien_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe actuel'
        }),
        label='Mot de passe actuel'
    )
    nouveau_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        }),
        label='Nouveau mot de passe'
    )
    confirmation_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le nouveau mot de passe'
        }),
        label='Confirmation du nouveau mot de passe'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_ancien_mot_de_passe(self):
        """Vérifier que l'ancien mot de passe est correct"""
        ancien_mot_de_passe = self.cleaned_data.get('ancien_mot_de_passe')
        if not self.user.check_password(ancien_mot_de_passe):
            raise ValidationError('Le mot de passe actuel est incorrect.')
        return ancien_mot_de_passe
    
    def clean(self):
        """Vérifier que les nouveaux mots de passe correspondent"""
        cleaned_data = super().clean()
        nouveau_mot_de_passe = cleaned_data.get('nouveau_mot_de_passe')
        confirmation_mot_de_passe = cleaned_data.get('confirmation_mot_de_passe')
        
        if nouveau_mot_de_passe and confirmation_mot_de_passe:
            if nouveau_mot_de_passe != confirmation_mot_de_passe:
                raise ValidationError('Les mots de passe ne correspondent pas.')
        
        return cleaned_data
    
    def save(self):
        """Changer le mot de passe"""
        nouveau_mot_de_passe = self.cleaned_data['nouveau_mot_de_passe']
        self.user.set_password(nouveau_mot_de_passe)
        self.user.save()
        return self.user
