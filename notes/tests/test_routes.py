from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

SLUG_NOTE_UNIQUE = 'slug1'

URL_ADD = reverse('notes:add')
URL_LIST = reverse('notes:list')
URL_EDIT = reverse('notes:edit', args=[SLUG_NOTE_UNIQUE])
URL_DETAIL = reverse('notes:detail', args=[SLUG_NOTE_UNIQUE])
URL_DELETE = reverse('notes:delete', args=[SLUG_NOTE_UNIQUE])
URL_SUCCESS = reverse('notes:success')
URL_HOME = reverse('notes:home')
URL_LOGIN = reverse('users:login')
URL_LOGOUT = reverse('users:logout')
URL_SIGNUP = reverse('users:signup')


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Пользователь-Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Пользователь-Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            author=cls.author,
            slug=SLUG_NOTE_UNIQUE
        )

        cls.URLS = (
            (URL_ADD, True, False),
            (URL_LIST, True, False),
            (URL_EDIT, False, False),
            (URL_DETAIL, False, False),
            (URL_DELETE, False, False),
            (URL_SUCCESS, True, False),
            (URL_HOME, True, True),
            (URL_LOGIN, True, True),
            (URL_LOGOUT, True, True),
            (URL_SIGNUP, True, True),
        )

    def test_urls_for_author(self):
        """
        Проверка доступов аутентифицированного пользователя, который
        является автором заметки.
        Страницы отдельной заметки, удаления и редактирования заметки
        должны быть доступны только автору.
        """
        for url, _, _ in self.URLS:
            with self.subTest(user=self.author, url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_non_author(self):
        """
        Проверка доступов аутентифицированного пользователя, который
        не является автором заметки.
        При попытке доступа к заметке - ошибка 404.
        """
        for url, non_author_access, _ in self.URLS:
            with self.subTest(user=self.reader, url=url):
                response = self.reader_client.get(url)
                if non_author_access:
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                else:
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )

    def test_urls_for_anonymous(self):
        """Проверка доступов неаутентифицированного пользователя.
        При попытке перейти на страницу списка заметок, страницу успешного
        добавления записи, страницу добавления заметки, отдельной заметки,
        редактирования или удаления заметки анонимный пользователь
        перенаправляется на страницу логина.
        """
        for url, _, anon_access in self.URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                if anon_access:
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                else:
                    redirect_url = f'{URL_LOGIN}?next={url}'
                    self.assertRedirects(response, redirect_url)
