"""Models du module `products`.

Inclut les modèles de cave, catégories, produits et l'historique des mouvements
de stock.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction, models


def generate_product_reference(product):
    """Génère une référence simple et lisible : REF-XXX-YYYY-NNN."""
    category_name = product.categorie.nom if product.categorie else "GENERAL"
    # Import local pour éviter tout risque de circular import
    from django.apps import apps
    from django.utils import timezone
    from django.utils.text import slugify

    category_code = (
        slugify(category_name).replace("-", "").upper()[:3].ljust(3, "X")
    )
    year = timezone.now().year

    produit_model = apps.get_model("products", "Produit")
    counter = (
        produit_model.objects.filter(
            categorie=product.categorie, date_creation__year=year
        ).count()
        + 1
    )

    return str(f"REF-{category_code}-{year}-{counter:03d}")




class Cave(models.Model):

    """
    Représente la cave principale de l'application.

    Même si le projet ne gère qu'une seule cave pour le moment,
    on garde ce modèle pour rester évolutif.
    """

    nom = models.CharField(max_length=150)
    adresse = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cave"
        verbose_name_plural = "Cave"

    def __str__(self) -> str:
        return str(self.nom)

    def clean(self):
        """

        Comme tu as précisé qu'il n'y a qu'une seule cave,
        on empêche la création de plusieurs lignes Cave.
        """
        if not self.pk and Cave.objects.exists():
            raise ValidationError("Une seule cave est autorisée dans cette version de l'application.")


class Categorie(models.Model):
    """
    Catégorise les produits : vin rouge, vin blanc, whisky, etc.
    L'icône est stockée comme une classe d'icône CSS (ex: lucide, fontawesome, bootstrap icons).
    """

    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=100, blank=True, help_text="Classe d'icône CSS")
    date_creation = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self) -> str:
        return str(self.nom)


class Fournisseur(models.Model):

    """
    Fournisseur de produits pour la cave.
    On garde des champs simples pour aller vite et rester clair.
    """

    nom = models.CharField(max_length=150)
    contact = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ["nom"]

    def __str__(self) -> str:
        return str(self.nom)



class Produit(models.Model):
    """
    Produit principal de la cave.

    La référence est générée automatiquement au premier enregistrement.
    Le stock actuel est stocké directement ici pour simplifier la gestion.
    """

    cave = models.ForeignKey(Cave, on_delete=models.PROTECT, related_name="produits")
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name="produits")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, related_name="produits")

    reference = models.CharField(max_length=30, unique=True, blank=True)
    nom = models.CharField(max_length=150)

    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2)

    stock_actuel = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5)

    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="produits/", blank=True, null=True)
    actif = models.BooleanField(default=True)
    est_supprime = models.BooleanField(default=False)
    date_suppression = models.DateTimeField(null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["nom"]

    def __str__(self) -> str:
        return str(f"{self.nom} ({self.reference})")


    @property
    def stock_faible(self):
        """
        Propriété de lecture pure.
        Elle ne modifie rien et sert uniquement à l'affichage.
        """
        return self.stock_actuel <= self.seuil_alerte

    @property
    def en_rupture(self):
        return self.stock_actuel == 0

    def save(self, *args, **kwargs):
        """Génération automatique de la référence."""
        if not self.reference:
            self.reference = generate_product_reference(self)
        super().save(*args, **kwargs)



class MouvementStock(models.Model):
    """
    Historise chaque mouvement de stock.
    Le stock du produit est mis à jour via un service dédié.
    """

    ENTREE = "ENTREE"
    SORTIE = "SORTIE"
    AJUSTEMENT = "AJUSTEMENT"

    TYPE_MOUVEMENT_CHOICES = [
        (ENTREE, "Entrée"),
        (SORTIE, "Sortie"),
        (AJUSTEMENT, "Ajustement"),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="mouvements")
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mouvements_stock",
    )

    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT_CHOICES)
    quantite = models.PositiveIntegerField()
    motif = models.CharField(max_length=255, blank=True)
    date_mouvement = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ["-date_mouvement"]

    def __str__(self) -> str:
        type_label = str(self.get_type_mouvement_display())  # type: ignore[attr-defined]
        produit_nom = str(getattr(self.produit, "nom", ""))
        return f"{type_label} - {produit_nom} - {self.quantite}"






    def clean(self):
        """On empêche les mouvements incohérents avant sauvegarde."""
        if self.quantite <= 0:
            raise ValidationError("La quantité doit être supérieure à zéro.")


        if self.type_mouvement == self.SORTIE:

            if self.quantite > self.produit.stock_actuel:
                raise ValidationError("La sortie ne peut pas dépasser le stock actuel.")


    def save(self, *args, **kwargs):
        """
        On sauvegarde d'abord le mouvement, puis on applique l'impact sur le stock.
        Cette logique est isolée dans un service pour rester propre.
        """
        with transaction.atomic():
            is_new = self._state.adding
            super().save(*args, **kwargs)

            if is_new:
                # Applique l'impact sur le stock directement dans le modèle.
                produit = self.produit
                if self.type_mouvement == self.ENTREE:
                    produit.stock_actuel += self.quantite
                elif self.type_mouvement == self.SORTIE:
                    if produit.stock_actuel < self.quantite:
                        raise ValidationError("La sortie ne peut pas dépasser le stock actuel.")
                    produit.stock_actuel -= self.quantite
                elif self.type_mouvement == self.AJUSTEMENT:
                    # Ajustement autorise des valeurs positives (et la clean peut être adaptée si besoin)
                    produit.stock_actuel += self.quantite

                produit.save(update_fields=["stock_actuel"])


from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=10, choices=[('light', 'Clair'), ('dark', 'Sombre')], default='light')

    def __str__(self):
        return f"Profil de {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()
