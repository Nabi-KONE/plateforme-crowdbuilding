"""
Modèles pour la gestion des notifications
Plateforme crowdBuilding - Burkina Faso
"""
from django.db import models
from django.utils import timezone
from apps.accounts.models import Utilisateur
from apps.projects.models import Projet
from apps.investments.models import Investissement


class TypeNotification(models.TextChoices):
    """Types de notifications"""
    VALIDATION_COMPTE = 'VALIDATION_COMPTE', 'Validation de compte'
    VALIDATION_PROJET = 'VALIDATION_PROJET', 'Validation de projet'
    NOUVEL_INVESTISSEMENT = 'NOUVEL_INVESTISSEMENT', 'Nouvel investissement'
    MISE_A_JOUR_PROJET = 'MISE_A_JOUR_PROJET', 'Mise à jour de projet'
    ALERTE_SYSTEME = 'ALERTE_SYSTEME', 'Alerte système'
    RAPPEL = 'RAPPEL', 'Rappel'
    CONFIRMATION_INVESTISSEMENT = 'CONFIRMATION_INVESTISSEMENT', 'Confirmation d\'investissement'
    REFUS_INVESTISSEMENT = 'REFUS_INVESTISSEMENT', 'Refus d\'investissement'
    PROJET_FINANCE = 'PROJET_FINANCE', 'Projet entièrement financé'
    ETAPE_TERMINEE = 'ETAPE_TERMINEE', 'Étape terminée'
    COMPTE_RENDU_PUBLIE = 'COMPTE_RENDU_PUBLIE', 'Compte rendu publié'


class Notification(models.Model):
    """
    Modèle pour les notifications du système
    """
    # Destinataire
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Utilisateur destinataire"
    )
    
    # Contenu
    titre = models.CharField(max_length=200, verbose_name="Titre")
    contenu = models.TextField(verbose_name="Contenu")
    type = models.CharField(
        max_length=30,
        choices=TypeNotification.choices,
        verbose_name="Type de notification"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name="Date de lecture")
    lue = models.BooleanField(default=False, verbose_name="Lue")
    
    # Relations optionnelles pour contextualiser la notification
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name="Projet concerné"
    )
    investissement = models.ForeignKey(
        Investissement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name="Investissement concerné"
    )
    
    # Action requise
    action_requise = models.BooleanField(default=False, verbose_name="Action requise")
    lien_action = models.URLField(blank=True, verbose_name="Lien d'action")
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'lue']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"{self.utilisateur.nom_complet} - {self.titre}"
    
    def marquer_comme_lue(self):
        """Marque la notification comme lue"""
        if not self.lue:
            self.lue = True
            self.date_lecture = timezone.now()
            self.save()
    
    def envoyer(self):
        """Envoie la notification (email + stockage en base)"""
        # Ici on pourrait ajouter l'envoi d'email
        # Pour l'instant, on se contente de sauvegarder en base
        self.save()
    
    @classmethod
    def creer_notification_validation_compte(cls, utilisateur, valide=True):
        """Crée une notification de validation de compte"""
        if valide:
            titre = "Compte validé avec succès"
            contenu = f"Bonjour {utilisateur.prenom},\n\nVotre compte a été validé avec succès. Vous pouvez maintenant utiliser toutes les fonctionnalités de la plateforme crowdBuilding."
            type_notif = TypeNotification.VALIDATION_COMPTE
        else:
            titre = "Validation de compte refusée"
            contenu = f"Bonjour {utilisateur.prenom},\n\nVotre demande de validation de compte a été refusée. Veuillez contacter l'administration pour plus d'informations."
            type_notif = TypeNotification.VALIDATION_COMPTE
        
        return cls.objects.create(
            utilisateur=utilisateur,
            titre=titre,
            contenu=contenu,
            type=type_notif
        )
    
    @classmethod
    def creer_notification_validation_projet(cls, projet, valide=True, motif=""):
        """Crée une notification de validation de projet"""
        if valide:
            titre = "Projet validé avec succès"
            contenu = f"Bonjour {projet.promoteur.prenom},\n\nVotre projet '{projet.titre}' a été validé avec succès. Il est maintenant visible sur la plateforme et peut recevoir des investissements."
            type_notif = TypeNotification.VALIDATION_PROJET
        else:
            titre = "Validation de projet refusée"
            contenu = f"Bonjour {projet.promoteur.prenom},\n\nVotre projet '{projet.titre}' a été refusé.\n\nMotif: {motif}\n\nVeuillez corriger les points mentionnés et soumettre à nouveau votre projet."
            type_notif = TypeNotification.VALIDATION_PROJET
        
        return cls.objects.create(
            utilisateur=projet.promoteur,
            titre=titre,
            contenu=contenu,
            type=type_notif,
            projet=projet
        )
    
    @classmethod
    def creer_notification_nouvel_investissement(cls, investissement):
        """Crée une notification pour un nouvel investissement"""
        titre = "Nouvel investissement reçu"
        contenu = f"Bonjour {investissement.projet.promoteur.prenom},\n\nVotre projet '{investissement.projet.titre}' a reçu un nouvel investissement de {investissement.montant:,.0f} FCFA de la part de {investissement.investisseur.nom_complet}."
        
        return cls.objects.create(
            utilisateur=investissement.projet.promoteur,
            titre=titre,
            contenu=contenu,
            type=TypeNotification.NOUVEL_INVESTISSEMENT,
            projet=investissement.projet,
            investissement=investissement
        )
    
    @classmethod
    def creer_notification_projet_finance(cls, projet):
        """Crée une notification quand un projet est entièrement financé"""
        titre = "Projet entièrement financé !"
        contenu = f"Félicitations {projet.promoteur.prenom} !\n\nVotre projet '{projet.titre}' a atteint 100% de son objectif de financement. Vous pouvez maintenant commencer la réalisation du projet."
        
        return cls.objects.create(
            utilisateur=projet.promoteur,
            titre=titre,
            contenu=contenu,
            type=TypeNotification.PROJET_FINANCE,
            projet=projet
        )
    
    @classmethod
    def creer_notification_etape_terminee(cls, etape):
        """Crée une notification quand une étape est terminée"""
        titre = "Étape terminée"
        contenu = f"L'étape '{etape.titre}' du projet '{etape.projet.titre}' a été terminée avec succès."
        
        # Notifier tous les investisseurs du projet
        investisseurs = Utilisateur.objects.filter(
            investissements__projet=etape.projet,
            investissements__statut='CONFIRME'
        ).distinct()
        
        notifications = []
        for investisseur in investisseurs:
            notifications.append(cls(
                utilisateur=investisseur,
                titre=titre,
                contenu=contenu,
                type=TypeNotification.ETAPE_TERMINEE,
                projet=etape.projet
            ))
        
        return cls.objects.bulk_create(notifications)
    
    @classmethod
    def creer_notification_compte_rendu(cls, compte_rendu):
        """Crée une notification quand un compte rendu est publié"""
        titre = "Nouveau compte rendu publié"
        contenu = f"Un nouveau compte rendu a été publié pour le projet '{compte_rendu.projet.titre}'.\n\nTitre: {compte_rendu.titre}\nAvancement: {compte_rendu.avancement}%"
        
        # Notifier tous les investisseurs du projet
        investisseurs = Utilisateur.objects.filter(
            investissements__projet=compte_rendu.projet,
            investissements__statut='CONFIRME'
        ).distinct()
        
        notifications = []
        for investisseur in investisseurs:
            notifications.append(cls(
                utilisateur=investisseur,
                titre=titre,
                contenu=contenu,
                type=TypeNotification.COMPTE_RENDU_PUBLIE,
                projet=compte_rendu.projet
            ))
        
        return cls.objects.bulk_create(notifications)
    
    @classmethod
    def get_notifications_non_lues(cls, utilisateur):
        """Retourne les notifications non lues d'un utilisateur"""
        return cls.objects.filter(utilisateur=utilisateur, lue=False)
    
    @classmethod
    def get_notifications_recentes(cls, utilisateur, limit=10):
        """Retourne les notifications récentes d'un utilisateur"""
        return cls.objects.filter(utilisateur=utilisateur)[:limit]
