from django.utils import timezone
from django.utils.text import slugify
from .models import Produit


def generate_product_reference(product):
    """
    Génère une référence simple et lisible :
    REF-XXX-YYYY-NNN

    - XXX : code de catégorie
    - YYYY : année courante
    - NNN : compteur séquentiel pour cette catégorie et cette année

    Cette logique est volontairement simple pour aller vite.
    On pourra l'améliorer plus tard si besoin.
    """
    category_name = product.categorie.nom if product.categorie else "GENERAL"
    category_code = slugify(category_name).replace("-", "").upper()[:3].ljust(3, "X")
    year = timezone.now().year

    counter = (
        Produit.objects.filter(categorie=product.categorie, date_creation__year=year).count() + 1
    )

    return f"REF-{category_code}-{year}-{counter:03d}"