from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.db.models import F, Count
from django.db.models.deletion import ProtectedError
from datetime import timedelta
from .models import Cave, Categorie, Fournisseur, Produit, MouvementStock, UserProfile
from .forms import ProduitForm, CategorieForm, FournisseurForm, MouvementStockForm, UserUpdateForm, UserProfileForm


# ─── Dashboard ───────────────────────────────────────────────

@login_required
def dashboard(request):
    # S'assurer que le profil de l'utilisateur connecté existe
    UserProfile.objects.get_or_create(user=request.user)

    aujourd_hui = timezone.now()
    il_y_a_30j = aujourd_hui - timedelta(days=30)

    # Exclure les produits supprimés logiquement
    produits = Produit.objects.filter(actif=True, est_supprime=False)
    total_produits = produits.count()
    total_categories = Categorie.objects.count()
    total_fournisseurs = Fournisseur.objects.filter(actif=True).count()

    stock_faible = produits.filter(stock_actuel__gt=0, stock_actuel__lte=F('seuil_alerte'))
    rupture = produits.filter(stock_actuel__lte=0)
    stock_faible_count = stock_faible.count()
    rupture_count = rupture.count()

    mouvements_30j = MouvementStock.objects.filter(date_mouvement__gte=il_y_a_30j).count()
    derniers_mouvements = MouvementStock.objects.select_related('produit', 'utilisateur')[:5]

    # Produits en alerte = stock faible + rupture
    produits_alerte = produits.filter(
        stock_actuel__lte=F('seuil_alerte')
    ).order_by('stock_actuel')[:5]

    # Produits pour le tableau d'état du stock
    produits_stock = produits.order_by('stock_actuel')[:5]

    context = {
        'total_produits': total_produits,
        'total_categories': total_categories,
        'total_fournisseurs': total_fournisseurs,
        'stock_faible_count': stock_faible_count,
        'rupture_count': rupture_count,
        'mouvements_30j': mouvements_30j,
        'produits_stock': produits_stock,
        'derniers_mouvements': derniers_mouvements,
        'produits_alerte': produits_alerte,
    }
    return render(request, 'products/dashboard.html', context)


# ─── Produits CRUD ───────────────────────────────────────────

@login_required
def produit_list(request):
    q = request.GET.get('q', '').strip()
    alerte = request.GET.get('alerte', '').strip()
    stock_faible = request.GET.get('stock_faible', '').strip()
    rupture = request.GET.get('rupture', '').strip()

    produits = Produit.objects.filter(est_supprime=False).select_related('categorie', 'fournisseur')

    if q:
        produits = produits.filter(
            models.Q(nom__icontains=q) |
            models.Q(reference__icontains=q) |
            models.Q(categorie__nom__icontains=q) |
            models.Q(fournisseur__nom__icontains=q)
        )

    if alerte == '1' or alerte == 'true':
        produits = produits.filter(stock_actuel__lte=F('seuil_alerte'))
    elif stock_faible == '1':
        produits = produits.filter(stock_actuel__gt=0, stock_actuel__lte=F('seuil_alerte'))
    elif rupture == '1':
        produits = produits.filter(stock_actuel__lte=0)

    active_filters = {
        'q': q,
        'alerte': alerte in ('1', 'true'),
        'stock_faible': stock_faible == '1',
        'rupture': rupture == '1'
    }
    has_active_filter = any(active_filters.values())

    context = {
        'produits': produits,
        'q': q,
        'active_filters': active_filters,
        'has_active_filter': has_active_filter
    }
    return render(request, 'products/produits/list.html', context)


@login_required
def produit_detail(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    mouvements = produit.mouvements.select_related('utilisateur').order_by('-date_mouvement')[:10]
    return render(request, 'products/produits/detail.html', {'produit': produit, 'mouvements': mouvements})


@login_required
def produit_create(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save(commit=False)
            cave = Cave.objects.first()
            if not cave:
                cave = Cave.objects.create(nom='Cave Principale')
            produit.cave = cave
            produit.save()
            messages.success(request, f'Produit "{produit.nom}" créé avec succès.')
            return redirect('produit_list')
    else:
        form = ProduitForm()
    return render(request, 'products/produits/form.html', {'form': form, 'titre': 'Ajouter un produit'})


@login_required
def produit_update(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produit "{produit.nom}" modifié avec succès.')
            return redirect('produit_detail', pk=produit.pk)
    else:
        form = ProduitForm(instance=produit)
    return render(request, 'products/produits/form.html', {'form': form, 'titre': 'Modifier le produit', 'produit': produit})


@login_required
def produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.est_supprime = True
        produit.date_suppression = timezone.now()
        produit.save()
        messages.success(request, f'Produit "{nom}" supprimé.')
        return redirect('produit_list')
    return render(request, 'products/produits/delete.html', {'produit': produit})


# ─── Catégories CRUD ─────────────────────────────────────────

@login_required
def categorie_list(request):
    categories = Categorie.objects.annotate(
        nb_produits=Count('produits', filter=models.Q(produits__est_supprime=False))
    ).all()
    return render(request, 'products/categories/list.html', {'categories': categories})


@login_required
def categorie_create(request):
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie créée avec succès.')
            return redirect('categorie_list')
    else:
        form = CategorieForm()
    return render(request, 'products/categories/form.html', {'form': form, 'titre': 'Nouvelle catégorie'})


@login_required
def categorie_update(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie modifiée avec succès.')
            return redirect('categorie_list')
    else:
        form = CategorieForm(instance=categorie)
    return render(request, 'products/categories/form.html', {'form': form, 'titre': 'Modifier la catégorie', 'categorie': categorie})


@login_required
def categorie_delete(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if categorie.produits.filter(est_supprime=False).exists():
        messages.error(request, f'Impossible de supprimer la catégorie "{categorie.nom}" car elle contient des produits actifs.')
        return redirect('categorie_list')

    if request.method == 'POST':
        try:
            categorie.delete()
            messages.success(request, 'Catégorie supprimée.')
            return redirect('categorie_list')
        except ProtectedError:
            messages.error(request, 'Impossible de supprimer cette catégorie car elle est référencée par des éléments du système.')
            return redirect('categorie_list')
    return render(request, 'products/categories/delete.html', {'categorie': categorie})


# ─── Fournisseurs CRUD ───────────────────────────────────────

@login_required
def fournisseur_list(request):
    fournisseurs = Fournisseur.objects.annotate(
        nb_produits=Count('produits')
    ).all()
    return render(request, 'products/fournisseurs/list.html', {'fournisseurs': fournisseurs})


@login_required
def fournisseur_create(request):
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur créé avec succès.')
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm()
    return render(request, 'products/fournisseurs/form.html', {'form': form, 'titre': 'Nouveau fournisseur'})


@login_required
def fournisseur_update(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur modifié avec succès.')
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)
    return render(request, 'products/fournisseurs/form.html', {'form': form, 'titre': 'Modifier le fournisseur', 'fournisseur': fournisseur})


@login_required
def fournisseur_delete(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if fournisseur.produits.filter(est_supprime=False).exists():
        messages.error(request, f'Impossible de supprimer le fournisseur "{fournisseur.nom}" car il est associé à des produits actifs.')
        return redirect('fournisseur_list')

    if request.method == 'POST':
        try:
            fournisseur.delete()
            messages.success(request, 'Fournisseur supprimé.')
            return redirect('fournisseur_list')
        except ProtectedError:
            messages.error(request, 'Impossible de supprimer ce fournisseur car il est référencée par des éléments du système.')
            return redirect('fournisseur_list')
    return render(request, 'products/fournisseurs/delete.html', {'fournisseur': fournisseur})


# ─── Mouvements de Stock ─────────────────────────────────────

@login_required
def mouvement_list(request):
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').all()
    return render(request, 'products/mouvements/list.html', {'mouvements': mouvements})


def _process_mouvement(request, type_mouvement):
    """Helper pour traiter un mouvement de stock."""
    titres = {
        'ENTREE': 'Entrée de stock',
        'SORTIE': 'Sortie de stock',
        'AJUSTEMENT': 'Ajustement de stock',
    }
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = type_mouvement
            mouvement.utilisateur = request.user

            produit = mouvement.produit
            if type_mouvement == 'ENTREE':
                produit.stock_actuel += mouvement.quantite
            elif type_mouvement == 'SORTIE':
                if produit.stock_actuel < mouvement.quantite:
                    messages.error(request, 'Stock insuffisant pour cette sortie.')
                    return render(request, 'products/mouvements/form.html', {
                        'form': form, 'titre': titres[type_mouvement], 'type_mouvement': type_mouvement
                    })
                produit.stock_actuel -= mouvement.quantite
            elif type_mouvement == 'AJUSTEMENT':
                produit.stock_actuel += mouvement.quantite  # Can be negative

            produit.save()
            mouvement.save()
            messages.success(request, f'{titres[type_mouvement]} enregistré(e) avec succès.')
            return redirect('mouvement_list')
    else:
        form = MouvementStockForm()
    return render(request, 'products/mouvements/form.html', {
        'form': form, 'titre': titres[type_mouvement], 'type_mouvement': type_mouvement
    })


@login_required
def stock_entree(request):
    return _process_mouvement(request, 'ENTREE')


@login_required
def stock_sortie(request):
    return _process_mouvement(request, 'SORTIE')


@login_required
def stock_ajustement(request):
    return _process_mouvement(request, 'AJUSTEMENT')


@login_required
def settings_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    active_tab = request.GET.get('tab', 'profile')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_profile':
            user_form = UserUpdateForm(request.POST, instance=user)
            profile_form = UserProfileForm(instance=profile)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Informations de profil mises à jour avec succès.')
                return redirect('/settings/?tab=profile')
        elif action == 'update_preferences':
            user_form = UserUpdateForm(instance=user)
            profile_form = UserProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Préférences mises à jour avec succès.')
                return redirect('/settings/?tab=preferences')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'active_tab': active_tab,
    }
    return render(request, 'products/settings.html', context)
