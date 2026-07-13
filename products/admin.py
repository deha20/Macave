from django.contrib import admin
from .models import Cave, Categorie, Fournisseur, Produit, MouvementStock


@admin.register(Cave)
class CaveAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour la cave.
    On garde une vue claire et rapide.
    """
    list_display = ("nom", "telephone", "email", "date_creation")
    search_fields = ("nom", "telephone", "email")
    list_filter = ("date_creation",)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "icone", "date_creation")
    search_fields = ("nom",)
    list_filter = ("date_creation",)


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ("nom", "contact", "telephone", "email", "actif", "date_creation")
    search_fields = ("nom", "contact", "telephone", "email")
    list_filter = ("actif", "date_creation")


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "reference",
        "categorie",
        "fournisseur",
        "stock_actuel",
        "seuil_alerte",
        "actif",
    )
    search_fields = ("nom", "reference")
    list_filter = ("categorie", "fournisseur", "actif")
    autocomplete_fields = ("cave", "categorie", "fournisseur")


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("produit", "type_mouvement", "quantite", "utilisateur", "date_mouvement")
    search_fields = ("produit__nom", "motif")
    list_filter = ("type_mouvement", "date_mouvement")