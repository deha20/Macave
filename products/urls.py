from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Produits
    path('produits/', views.produit_list, name='produit_list'),
    path('produits/ajouter/', views.produit_create, name='produit_create'),
    path('produits/<int:pk>/', views.produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/', views.produit_update, name='produit_update'),
    path('produits/<int:pk>/supprimer/', views.produit_delete, name='produit_delete'),

    # Catégories
    path('categories/', views.categorie_list, name='categorie_list'),
    path('categories/ajouter/', views.categorie_create, name='categorie_create'),
    path('categories/<int:pk>/modifier/', views.categorie_update, name='categorie_update'),
    path('categories/<int:pk>/supprimer/', views.categorie_delete, name='categorie_delete'),

    # Fournisseurs
    path('fournisseurs/', views.fournisseur_list, name='fournisseur_list'),
    path('fournisseurs/ajouter/', views.fournisseur_create, name='fournisseur_create'),
    path('fournisseurs/<int:pk>/modifier/', views.fournisseur_update, name='fournisseur_update'),
    path('fournisseurs/<int:pk>/supprimer/', views.fournisseur_delete, name='fournisseur_delete'),

    # Stock
    path('stock/entree/', views.stock_entree, name='stock_entree'),
    path('stock/sortie/', views.stock_sortie, name='stock_sortie'),
    path('stock/ajustement/', views.stock_ajustement, name='stock_ajustement'),

    # Mouvements
    path('mouvements/', views.mouvement_list, name='mouvement_list'),

    # Paramètres
    path('settings/', views.settings_view, name='settings'),
]
