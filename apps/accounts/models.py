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
        default=StatutCompte.ACTIF,
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
    
    def get_role_actif(self):
        """Retourne le rôle actif de l'utilisateur"""
        return self.roles.filter(role_actif=True).first()
    
    def est_investisseur(self):
        """Vérifie si l'utilisateur est un investisseur validé"""
        role = self.get_role_actif()
        return (role and 
                role.type == TypeRole.INVESTISSEUR and 
                role.statut == StatutRole.VALIDE)
    
    def est_promoteur(self):
        """Vérifie si l'utilisateur est un promoteur validé"""
        role = self.get_role_actif()
        return (role and 
                role.type == TypeRole.PROMOTEUR and 
                role.statut == StatutRole.VALIDE)
    
    def est_administrateur(self):
        """Vérifie si l'utilisateur est un administrateur"""
        return self.is_staff and self.is_superuser


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
    
    def valider(self):
        """Valider le rôle"""
        self.statut = StatutRole.VALIDE
        self.save()
    
    def refuser(self):
        """Refuser le rôle"""
        self.statut = StatutRole.REFUSE
        self.save()
    
    def suspendre(self):
        """Suspendre le rôle"""
        self.statut = StatutRole.SUSPENDU
        self.save()
