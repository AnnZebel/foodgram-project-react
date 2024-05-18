from django.contrib import admin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    def favorites_count(self, obj):
        return obj.favorites.count()

    favorites_count.short_description = 'Количество в избранном'

    list_display = ('pk', 'name', 'author', 'favorites_count',
                    'text', 'cooking_time', 'image')
    list_editable = (
        'name', 'cooking_time', 'text', 'image'
    )
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')
