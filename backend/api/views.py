from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Follow
from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers import (FavoriteOrShoppingCartSerializer,
                             FollowSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             TagSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    @action(detail=True, methods=['post', 'delete'],
            serializer_class=FollowSerializer)
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if self.request.method == 'POST':
            if user == author:
                raise exceptions.ValidationError(
                    'Нельзя подписаться на самого себя!'
                )
            if Follow.objects.filter(
                user=user,
                author=author
            ).exists():
                raise exceptions.ValidationError(
                    'Вы уже подписаны на этого автора.'
                )
            Follow.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not Follow.objects.filter(
                user=user,
                author=author
            ).exists():
                raise exceptions.ValidationError(
                    'Подписка не была оформлена, либо уже удалена.'
                )
            subscription = get_object_or_404(
                Follow,
                user=user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'],
            serializer_class=FollowSerializer,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = self.request.user
        subscriptions = User.objects.filter(
            following__user=user
        ).prefetch_related('recipes')
        paginated_queryset = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise exceptions.AuthenticationFailed(
                'Пользователь не авторизован')
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({
                'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        if request.method == "POST":
            if Favorite.objects.filter(user=request.user,
                                       recipe=recipe).exists():
                return Response({
                    'error': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = FavoriteOrShoppingCartSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe).first()
            if favorite is None:
                return Response({
                    'error': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({
                'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                return Response({
                    'error': 'Рецепт уже добавлен в список покупок.'},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = FavoriteOrShoppingCartSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            if not ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                raise exceptions.ValidationError(
                    'Рецепта нет в списке покупок.'
                )
            shopping_cart = get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=recipe
            )
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        shopping_list = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_total=Sum('amount'))

        text = 'Список покупок:\n\n'
        for item in shopping_list:
            text += (
                f'{item["ingredient__name"]}: {item["ingredient_total"]}'
                f' {item["ingredient__measurement_unit"]}\n'
            )
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
