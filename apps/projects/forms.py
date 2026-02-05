from django import forms
from .models import CompteRendu, Projet, Etape, DocumentObligatoire, ImageProjet, DocumentProjet
from django.core.exceptions import ValidationError
import datetime
from decimal import Decimal
from django.urls import reverse  
  
ImageProjetFormSet = forms.inlineformset_factory(
    Projet,
    ImageProjet,
    fields=('image', 'legende', 'est_principale'),
    extra=1,
    can_delete=True
)

DocumentProjetFormSet = forms.inlineformset_factory(
    Projet,
    DocumentProjet,
    fields=('type_document', 'nom', 'fichier', 'description', 'est_public'),
    extra=1,
    can_delete=True
)

class NouveauProjetForm(forms.ModelForm):
    nombre_total_parts = forms.IntegerField(
        required=True,
        min_value=10,
        max_value=100000,
        initial=1000,
        label="Nombre total de parts",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_nombre_total_parts',
            'min': '10',
            'max': '100000',
            'step': '1'
        })
    )

    nombre_min_parts = forms.IntegerField(
        required=True,
        min_value=1,
        initial=1,
        label="Nombre minimum de parts par investisseur",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_nombre_min_parts',
            'min': '1',
            'step': '1'
        }),
        help_text="Nombre minimum de parts qu'un investisseur doit souscrire"
    )

    
    prix_unitaire_affiche = forms.CharField(
        required=False,
        label="Prix unitaire d'une part (calculé)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_prix_unitaire_affiche',
            'readonly': 'readonly',
            'placeholder': 'Calculé automatiquement'
        })
    )
    
    
    duree_campagne = forms.IntegerField(
        required=True,
        initial=3,
        min_value=1,
        max_value=24,
        label="Durée de collecte (mois)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_duree_campagne',
            'min': '1',
            'max': '24',
            'step': '1'
        })
    )
    
    duree = forms.IntegerField(
        required=True,
        initial=12,
        min_value=1,
        max_value=60,
        label="Durée prévisionnelle de réalisation (mois)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_duree',
            'min': '1',
            'max': '60',
            'step': '1'
        })
    )
    
    document_foncier = forms.FileField(
        required=True,
        label="Titre de propriété ou document foncier *",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'id_document_foncier'
        })
    )
    
    document_technique = forms.FileField(
        required=True,
        label="Permis de construire / Document technique *",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
            'id': 'id_document_technique'
        })
    )
    
    document_financier = forms.FileField(
        required=True,
        label="Budget global *",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.xls,.xlsx,.doc,.docx',
            'id': 'id_document_financier'
        })
    )
    
    definir_etapes_maintenant = forms.BooleanField(
        required=False,
        initial=False,
        label="Définir les étapes maintenant",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_definir_etapes_maintenant'
        })
    )

    class Meta:
        model = Projet
        fields = [
            'titre', 'categorie', 'description',
            'montant_total',
            'nombre_min_parts',
            'date_debut',
            'localisation', 'ville', 'region',
            'image_garde',
        ]
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom public du projet',
                'id': 'id_titre'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Description détaillée du projet...',
                'id': 'id_description'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_categorie'
            }),
            'montant_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 50000000',
                'id': 'id_montant_total',
                'min': '100000'
            }),
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_date_debut'
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse / Parcelle',
                'id': 'id_localisation'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ouagadougou',
                'id': 'id_ville'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Centre',
                'id': 'id_region'
            }),
            'image_garde': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_image_garde'
            })
        }
        
        labels = {
            'titre': 'Titre du projet *',
            'categorie': 'Type de projet *',
            'description': 'Description détaillée *',
            'montant_total': 'Coût total de réalisation (FCFA) *',
            'date_debut': 'Date prévisionnelle de début de réalisation *',
            'localisation': 'Adresse / Parcelle *',
            'ville': 'Ville *',
            'region': 'Région *',
            'image_garde': 'Image de garde',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            date_debut = datetime.date.today()
            self.initial.update({
                'date_debut': date_debut,
                'nombre_total_parts': 1000,
                'seuil_declenchement': Decimal('100.00'),
                'duree_campagne': 3,
                'duree': 12,
                'ville': 'Ouagadougou',
                'region': 'Centre',
            })
        
        
        if self.instance.pk and self.instance.montant_total and self.instance.nombre_total_parts:
            valeur_part = self.instance.montant_total / self.instance.nombre_total_parts
            self.initial['prix_unitaire_affiche'] = f"{valeur_part:,.0f} FCFA"
            self.initial['prix_unitaire'] = valeur_part
        else:
            self.initial['prix_unitaire_affiche'] = "Calculé automatiquement"

    def clean(self):
        cleaned_data = super().clean()
        
        montant_total = cleaned_data.get('montant_total')
        nombre_total_parts = cleaned_data.get('nombre_total_parts')
        
        if montant_total and nombre_total_parts:
            # Calculer le prix unitaire
            prix_unitaire_calcule = montant_total / nombre_total_parts
            
            # Validation du prix minimum (100 FCFA)
            if prix_unitaire_calcule < 100:
                self.add_error('montant_total', 
                    f"Le prix unitaire calculé serait de {prix_unitaire_calcule:,.0f} FCFA. "
                    f"Le prix minimum d'une part est de 100 FCFA.")
                self.add_error('nombre_total_parts',
                    f"Avec ce nombre de parts, le prix unitaire est trop bas.")
            
            # Validation du prix maximum (optionnel)
            if prix_unitaire_calcule > 1000000:
                self.add_error('montant_total',
                    f"Le prix unitaire calculé est très élevé ({prix_unitaire_calcule:,.0f} FCFA). "
                    f"Vérifiez vos chiffres.")
                
        nombre_total_parts = cleaned_data.get('nombre_total_parts')
        nombre_min_parts = cleaned_data.get('nombre_min_parts')

        if nombre_min_parts and nombre_total_parts:
            if nombre_min_parts > nombre_total_parts:
                self.add_error('nombre_min_parts',
                    "Le nombre minimum de parts ne peut pas dépasser le nombre total de parts")
                
        
        date_debut = cleaned_data.get('date_debut')
        if date_debut and date_debut <= datetime.date.today():
            raise ValidationError(
                "La date de début de réalisation doit être postérieure à la date du jour"
            )
        
        duree_campagne = cleaned_data.get('duree_campagne')
        if duree_campagne and (duree_campagne < 1 or duree_campagne > 24):
            raise ValidationError("La durée de collecte doit être comprise entre 1 et 24 mois")
        
        if not cleaned_data.get('document_foncier') and not self.instance.pk:
            raise ValidationError("Le document foncier est obligatoire")
        if not cleaned_data.get('document_technique') and not self.instance.pk:
            raise ValidationError("Le permis de construire/document technique est obligatoire")
        if not cleaned_data.get('document_financier') and not self.instance.pk:
            raise ValidationError("Le budget global est obligatoire")
        
        return cleaned_data
    
    def clean_document_foncier(self):
        return self._valider_document(
            self.cleaned_data.get('document_foncier'),
            ['pdf', 'jpg', 'jpeg', 'png'],
            10,
            "Document foncier"
        )
    
    def clean_document_technique(self):
        return self._valider_document(
            self.cleaned_data.get('document_technique'),
            ['pdf', 'jpg', 'jpeg', 'png'],
            10,
            "Document technique"
        )
    
    def clean_document_financier(self):
        return self._valider_document(
            self.cleaned_data.get('document_financier'),
            ['pdf', 'xls', 'xlsx', 'doc', 'docx'],
            10,
            "Budget global"
        )
    
    def _valider_document(self, document, extensions_autorisees, taille_max_mb, nom_document):
        if document:
            if document.size > taille_max_mb * 1024 * 1024:
                raise ValidationError(
                    f"{nom_document} : Le fichier ne doit pas dépasser {taille_max_mb}MB."
                )
            
            ext = document.name.split('.')[-1].lower()
            if ext not in extensions_autorisees:
                raise ValidationError(
                    f"{nom_document} : Format de fichier non supporté. "
                    f"Formats acceptés: {', '.join(extensions_autorisees)}."
                )
        return document
    

    def save(self, commit=True):
        projet = super().save(commit=False)
        
        # Ajouter les champs supplémentaires
        projet.nombre_total_parts = self.cleaned_data.get('nombre_total_parts')
        projet.nombre_min_parts = self.cleaned_data.get('nombre_min_parts', 1)
        projet.duree_campagne = self.cleaned_data.get('duree_campagne')
        projet.duree = self.cleaned_data.get('duree')
        
        # FORCER le seuil de déclenchement à 100%
        projet.seuil_declenchement = Decimal('100.00')
        
        # Calculer le prix unitaire
        if projet.montant_total and projet.nombre_total_parts:
            projet.prix_unitaire = projet.montant_total / projet.nombre_total_parts
        else:
            # Valeur par défaut sécurisée
            projet.prix_unitaire = Decimal('0.00')
        
        # Calculer la date de fin (ajouter des mois)
        if projet.date_debut and projet.duree:
            projet.date_fin = self._ajouter_mois(projet.date_debut, projet.duree)
        
        if commit:
            projet.save()
            self._sauvegarder_documents(projet)
        
        return projet
    
    def _ajouter_mois(self, date, mois):
        import datetime
        month = date.month - 1 + mois
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(date.day, [31,
            29 if year % 4 == 0 and (not year % 100 == 0 or year % 400 == 0) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return datetime.date(year, month, day)
    
    def _sauvegarder_documents(self, projet):
        from .models import DocumentObligatoire
        
        documents_data = [
            ('PERMIS_CONSTRUIRE', self.cleaned_data.get('document_foncier'), 
             'Document foncier - Titre de propriété'),
            ('TECHNIQUE', self.cleaned_data.get('document_technique'), 
             'Document technique - Permis de construire'),
            ('BUSINESS_PLAN', self.cleaned_data.get('document_financier'), 
             'Document financier - Budget global'),
        ]
        
        for doc_type, fichier, nom in documents_data:
            if fichier:
                DocumentObligatoire.objects.create(
                    projet=projet,
                    type_document=doc_type,
                    nom=nom,
                    fichier=fichier,
                    est_obligatoire=True,
                    description=f"Document soumis lors de la création du projet"
                )


from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .models import CompteRendu, ImageCompteRendu, Projet, Etape
from django.forms import inlineformset_factory

# ============================================
# FORMULAIRE IMAGE COMPTE RENDU
# ============================================

class ImageCompteRenduForm(forms.ModelForm):
    """Formulaire pour une image de compte rendu"""
    class Meta:
        model = ImageCompteRendu
        fields = ['image', 'legende']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control image-upload-input',
                'accept': 'image/jpeg,image/png,image/webp',
                'data-max-size': '10485760'  # 10MB en bytes
            }),
            'legende': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description de l\'image...',
                'maxlength': '200'
            }),
        }
        labels = {
            'image': 'Fichier image *',
            'legende': 'Légende (optionnel)',
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier le type MIME
            content_type = image.content_type
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if content_type not in allowed_types:
                raise ValidationError(
                    f"Format non supporté. Formats acceptés: JPEG, PNG, WebP."
                )
            
            # Vérifier l'extension
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise ValidationError(
                    f"Extension non supportée. Extensions acceptées: .jpg, .jpeg, .png, .webp"
                )
        
        return image

# ============================================
# FORMSET POUR LES IMAGES
# ============================================

ImageCompteRenduFormSet = inlineformset_factory(
    CompteRendu,
    ImageCompteRendu,
    form=ImageCompteRenduForm,
    extra=1,  # 1 formulaire vide par défaut
    can_delete=True,
    max_num=10,  # Maximum 10 images
    min_num=1,   # Minimum 1 image
    validate_min=True,
    validate_max=True,
)

# ============================================
# FORMULAIRE COMPTE RENDU PRINCIPAL
# ============================================

class CompteRenduForm(forms.ModelForm):
    """Formulaire principal pour soumettre un compte rendu"""
    
    # Champ pour les images (géré séparément par le formset)
    images = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'images_data'}),
        help_text="Images uploadées"
    )
    
    # Redéfinir le champ avancement avec un widget caché
    avancement = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        initial=0,
        widget=forms.HiddenInput(attrs={'id': 'id_avancement'}),
        label="Avancement global (%)",
        help_text="Pourcentage d'avancement depuis le dernier compte rendu"
    )
    
    class Meta:
        model = CompteRendu
        fields = ['projet', 'etape', 'titre', 'contenu', 'avancement']
        widgets = {
            'projet': forms.Select(attrs={
                'class': 'form-select',
                'style': 'height: 50px;',
                'id': 'id_projet',
                'required': 'required'
            }),
            'etape': forms.Select(attrs={
                'class': 'form-select',
                'style': 'height: 50px;',
                'id': 'id_etape'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Rapport d\'avancement - Phase 1',
                'style': 'height: 50px;',
                'maxlength': '200',
                'id': 'id_titre'
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Décrivez en détail l\'avancement du projet (minimum 200 caractères)...',
                'id': 'id_contenu',
                'minlength': '200'
            }),
            # avancement est défini séparément
        }
        labels = {
            'projet': 'Projet *',
            'etape': 'Étape concernée (optionnel)',
            'titre': 'Titre du compte rendu *',
            'contenu': 'Contenu détaillé *',
            'avancement': 'Avancement global (%) *',
        }
        help_texts = {
            'contenu': 'Minimum 200 caractères',
            'avancement': 'Pourcentage d\'avancement depuis le dernier compte rendu',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.projet_pre_selectionne = kwargs.pop('projet_pre_selectionne', None)
        super().__init__(*args, **kwargs)
        
        # Si un projet est pré-sélectionné, le fixer et désactiver le champ
        if self.projet_pre_selectionne:
            self.fields['projet'].initial = self.projet_pre_selectionne
            self.fields['projet'].disabled = True
            self.fields['projet'].widget.attrs['readonly'] = True
            self.fields['projet'].widget.attrs['class'] += ' bg-light'
            self.fields['projet'].help_text = "Projet sélectionné depuis la page détail"
        
        # Filtrer les projets
        if self.user and self.user.est_promoteur():
            self.fields['projet'].queryset = self.user.projets.filter(
                statut__in=['EN_COURS_EXECUTION', 'FINANCE', 'EN_CAMPAGNE']
            ).order_by('-date_creation')
        else:
            self.fields['projet'].queryset = Projet.objects.none()
        
        # Filtrer les étapes selon le projet sélectionné ou initial
        projet = None
        if self.instance and self.instance.pk:
            projet = self.instance.projet
        elif self.projet_pre_selectionne:
            projet = self.projet_pre_selectionne
        elif 'projet' in self.data:  # Si le formulaire a été soumis
            try:
                projet_id = self.data.get('projet')
                if projet_id:
                    projet = Projet.objects.get(id=projet_id)
            except (ValueError, Projet.DoesNotExist):
                pass
        
        if projet:
            self.fields['etape'].queryset = projet.etapes.all().order_by('ordre')
        else:
            self.fields['etape'].queryset = Etape.objects.none()
        
        # Définir l'URL pour charger les étapes en AJAX
        self.fields['projet'].widget.attrs['data-etapes-url'] = reverse('projects:ajax_get_etapes_projet')
        
        # Définir une valeur initiale pour l'avancement si elle n'existe pas
        if not self.initial.get('avancement'):
            self.initial['avancement'] = 0
    
    def clean_contenu(self):
        contenu = self.cleaned_data.get('contenu', '').strip()
        if len(contenu) < 200:
            raise ValidationError(
                f"Le contenu doit contenir au moins 200 caractères. "
                f"Actuellement : {len(contenu)} caractères."
            )
        return contenu
    
    def clean_avancement(self):
        avancement = self.cleaned_data.get('avancement')
        if avancement is None:
            raise ValidationError("L'avancement est requis.")
        
        try:
            avancement = float(avancement)
            if avancement < 0 or avancement > 100:
                raise ValidationError("L'avancement doit être compris entre 0 et 100%.")
        except (ValueError, TypeError):
            raise ValidationError("L'avancement doit être un nombre valide.")
        
        return avancement
    
    def clean(self):
        cleaned_data = super().clean()
        projet = cleaned_data.get('projet')
        etape = cleaned_data.get('etape')
        
        # Si projet est désactivé (pré-sélectionné), récupérer sa valeur
        if self.projet_pre_selectionne and not projet:
            cleaned_data['projet'] = self.projet_pre_selectionne
            projet = self.projet_pre_selectionne
        
        # Vérifier que l'étape appartient au projet
        if etape and projet and etape.projet != projet:
            self.add_error('etape', "Cette étape n'appartient pas au projet sélectionné.")
        
        # Vérifier que le projet peut recevoir des comptes rendus
        if projet and projet.statut not in ['EN_COURS_EXECUTION', 'FINANCE', 'EN_CAMPAGNE']:
            self.add_error('projet', f"Ce projet ({projet.get_statut_display()}) ne peut pas recevoir de comptes rendus.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sauvegarde le compte rendu"""
        compte_rendu = super().save(commit=False)
        
        # S'assurer que l'avancement est un Decimal
        if 'avancement' in self.cleaned_data:
            from decimal import Decimal
            avancement = self.cleaned_data['avancement']
            if isinstance(avancement, (int, float)):
                compte_rendu.avancement = Decimal(str(avancement))
        
        if commit:
            compte_rendu.save()
        
        return compte_rendu

# ============================================
# FORMULAIRE DE MODIFICATION
# ============================================

class CompteRenduModificationForm(CompteRenduForm):
    """Formulaire pour modifier un compte rendu existant"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pour la modification, on ne permet pas de changer le projet
        if self.instance and self.instance.pk:
            self.fields['projet'].disabled = True
            self.fields['projet'].widget.attrs['readonly'] = True
            self.fields['projet'].widget.attrs['class'] += ' bg-light'
            self.fields['projet'].help_text = "Le projet ne peut pas être modifié"
            
            # Pré-remplir les étapes du projet
            if self.instance.projet:
                self.fields['etape'].queryset = self.instance.projet.etapes.all().order_by('ordre')