"""
Modèles pour la gestion des utilisateurs et des rôles
Plateforme crowdBuilding - Burkina Faso
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class TypeRole(models.TextChoices):
    """Types de rôles disponibles sur la plateforme"""
    INVESTISSEUR = 'INVESTISSEUR', 'Investisseur'
    PROMOTEUR = 'PROMOTEUR', 'Promoteur'
    ADMINISTRATEUR = 'ADMINISTRATEUR', 'Administrateur'


class StatutRole(models.TextChoices):
    """Statuts possibles pour un rôle"""
    EN_ATTENTE_VALIDATION = 'EN_ATTENTE_VALIDATION', 'En attente de validation'
    VALIDE = 'VALIDE', 'Validé'
    REFUSE = 'REFUSE', 'Refusé'
    SUSPENDU = 'SUSPENDU', 'Suspendu'


class StatutCompte(models.TextChoices):
    """Statuts possibles pour un compte utilisateur"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente de validation'
    ACTIF = 'ACTIF', 'Actif'
    SUSPENDU = 'SUSPENDU', 'Suspendu'
    BLOQUE = 'BLOQUE', 'Bloqué'

class CustomUserManager(BaseUserManager):
    """Gestionnaire personnalisé pour les utilisateurs"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Créer un utilisateur standard"""
        if not email:
            raise ValueError('L\'email est obligatoire')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Créer un superutilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé
    L'email est utilisé comme identifiant unique
    """
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(unique=True, verbose_name="Email")
    telephone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?[0-9]{8,15}$',
            message='Format de téléphone invalide'
        )],
        verbose_name="Téléphone"
    )
    profession = models.CharField(max_length=100, blank=True, verbose_name="Profession")
    entreprise = models.CharField(max_length=100, blank=True, verbose_name="Entreprise")
    experience = models.TextField(blank=True, verbose_name="Expérience")
    date_inscription = models.DateTimeField(default=timezone.now, verbose_name="Date d'inscription")
    statut_compte = models.CharField(
        max_length=20,
        choices=StatutCompte.choices,
        default=StatutCompte.EN_ATTENTE,
        verbose_name="Statut du compte"
    )
    
    # Champs Django requis
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_inscription']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"
    
    @property
    def nom_complet(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.prenom} {self.nom}"
    
    def get_full_name(self):
        """
        Méthode requise par Django pour récupérer le nom complet
        Utilisée par l'admin Django et d'autres composants
        """
        return self.nom_complet
    
    def get_short_name(self):
        """
        Méthode requise par Django pour récupérer le nom court
        """
        return self.prenom
    
    def est_valide(self):
        """
        Vérifie si l'utilisateur est validé
        - Superuser est toujours validé
        - Les autres utilisateurs doivent avoir un rôle validé
        """
        if self.is_superuser:
            return True
        
        role_actif = self.get_role_actif()
        return role_actif and role_actif.statut == StatutRole.VALIDE
    
    def est_administrateur(self):
        """
        Vérifie si l'utilisateur est un administrateur
        - Soit superuser technique
        - Soit a un rôle administrateur validé
        """
        if self.is_superuser:
            return True
        
        role_admin = self.roles.filter(
            type=TypeRole.ADMINISTRATEUR,
            statut=StatutRole.VALIDE
        ).first()
        return role_admin is not None
    
    def get_role_actif(self):
        """Retourne le rôle actif de l'utilisateur"""
        if self.is_superuser:
            # Pour les superusers, créer un rôle admin virtuel
            return type('obj', (object,), {
                'type': TypeRole.ADMINISTRATEUR,
                'statut': StatutRole.VALIDE,
                'get_type_display': lambda: 'Administrateur',
                'role_actif': True
            })()
        
        return self.roles.filter(role_actif=True).first()
    
    def est_investisseur(self):
        """Vérifie si l'utilisateur est un investisseur validé"""
        if self.is_superuser:
            return False
        role = self.get_role_actif()
        return (role and 
                role.type == TypeRole.INVESTISSEUR and 
                role.statut == StatutRole.VALIDE)
    
    def est_promoteur(self):
        """Vérifie si l'utilisateur est un promoteur validé"""
        if self.is_superuser:
            return False
        role = self.get_role_actif()
        return (role and 
                role.type == TypeRole.PROMOTEUR and 
                role.statut == StatutRole.VALIDE)
    
    def mettre_a_jour_statut_compte(self):
        """
        Met à jour automatiquement le statut du compte en fonction du rôle actif
        """
        role_actif = self.get_role_actif()
        
        if not role_actif or not hasattr(role_actif, 'statut'):
            # Si pas de rôle, garder le statut actuel ou mettre EN_ATTENTE
            if self.statut_compte not in [StatutCompte.BLOQUE, StatutCompte.SUSPENDU]:
                self.statut_compte = StatutCompte.EN_ATTENTE
            return
            
        # Synchronisation basée sur le statut du rôle
        if role_actif.statut == StatutRole.VALIDE:
            self.statut_compte = StatutCompte.ACTIF
        elif role_actif.statut == StatutRole.REFUSE:
            self.statut_compte = StatutCompte.BLOQUE
        elif role_actif.statut == StatutRole.SUSPENDU:
            self.statut_compte = StatutCompte.SUSPENDU
        elif role_actif.statut == StatutRole.EN_ATTENTE_VALIDATION:
            self.statut_compte = StatutCompte.EN_ATTENTE
        
        self.save()


class Role(models.Model):
    """
    Modèle pour gérer les rôles des utilisateurs
    Un utilisateur peut avoir plusieurs rôles mais un seul actif à la fois
    """
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='roles',
        verbose_name="Utilisateur"
    )
    type = models.CharField(
        max_length=20,
        choices=TypeRole.choices,
        verbose_name="Type de rôle"
    )
    statut = models.CharField(
        max_length=25,
        choices=StatutRole.choices,
        default=StatutRole.EN_ATTENTE_VALIDATION,
        verbose_name="Statut du rôle"
    )
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    role_actif = models.BooleanField(default=True, verbose_name="Rôle actif")

    # ==== NOUVEAUX CHAMPS À AJOUTER ====
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    date_refus = models.DateTimeField(null=True, blank=True, verbose_name="Date de refus")
    date_suspension = models.DateTimeField(null=True, blank=True, verbose_name="Date de suspension")
    motif_refus = models.TextField(blank=True, verbose_name="Motif de refus")
    motif_suspension = models.TextField(blank=True, verbose_name="Motif de suspension")
    administrateur_validateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_valides',
        verbose_name="Administrateur validateur"
    )
    
    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        unique_together = ['utilisateur', 'type']  # Un utilisateur ne peut avoir qu'un rôle de chaque type
    
    def __str__(self):
        return f"{self.utilisateur.nom_complet} - {self.get_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save pour gérer les rôles actifs"""
        # Si ce rôle devient actif, désactiver les autres rôles de l'utilisateur
        if self.role_actif:
            Role.objects.filter(utilisateur=self.utilisateur).exclude(pk=self.pk).update(role_actif=False)
        
        super().save(*args, **kwargs)

        # Synchroniser le statut du compte utilisateur
        if self.role_actif:
            self.utilisateur.mettre_a_jour_statut_compte()
    
    def valider(self, administrateur):
        """Valider le rôle"""
        self.statut = StatutRole.VALIDE
        self.date_validation = timezone.now()
        self.administrateur_validateur = administrateur
        self.motif_refus = ""
        self.motif_suspension = ""
        self.save()
    
    def refuser(self, administrateur, motif):
        """Refuser le rôle"""
        self.statut = StatutRole.REFUSE
        self.date_refus = timezone.now()
        self.administrateur_validateur = administrateur
        self.motif_refus = motif
        self.motif_suspension = ""
        self.save()

    def suspendre(self, administrateur, motif):
        """Suspendre le rôle"""
        self.statut = StatutRole.SUSPENDU
        self.date_suspension = timezone.now()
        self.administrateur_validateur = administrateur
        self.motif_suspension = motif
        self.motif_refus = ""
        self.save()
    
    
