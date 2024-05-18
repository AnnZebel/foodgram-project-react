import base64

from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)
from rest_framework import serializers

from users.models import Follow


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "password")


class FollowSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name",
                  "is_subscribed", "recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', "name", "measurement_unit", "amount")


class RecipeIngredientCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('recipe', 'id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipes')
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user,
                                       recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientCreateUpdateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'author',
                  'name', 'text', 'cooking_time')
        lookup_field = 'author'

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле 'tags' не должно быть пустым.")
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return value

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингридиент для рецепта'})
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингредиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 1')
                })
        return data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        create_ingredients = [
            RecipeIngredient(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(create_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is None:
            raise serializers.ValidationError(
                {"tags": "Поле 'tags' обязательно для обновления рецепта."})
        instance.tags.set(tags)
        if ingredients is None:
            raise serializers.ValidationError(
                {"ingredients": "Поле 'ingredients' "
                                "обязательно для обновления рецепта."})
        instance.ingredients.clear()
        create_ingredients = [
            RecipeIngredient(
                ingredient=ingredient['ingredient'],
                recipe=instance,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(create_ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteOrShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
