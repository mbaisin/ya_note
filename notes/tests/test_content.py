from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()

SLUG_NOTE_1 = 'zametka1'

URL_ADD = reverse('notes:add')
URL_EDIT = reverse('notes:edit', args=[SLUG_NOTE_1])
URL_LIST = reverse('notes:list')


class TestPages(TestCase):
    """Тестирование контента."""

    @classmethod
    def setUpTestData(cls):
        cls.author_1 = User.objects.create(username='Пользователь-Автор-1')
        cls.author_2 = User.objects.create(username='Пользователь-Автор-2')
        cls.user_client_1 = Client()
        cls.user_client_1.force_login(cls.author_1)
        cls.user_client_2 = Client()
        cls.user_client_2.force_login(cls.author_2)
        cls.note_1 = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            author=cls.author_1,
            slug=SLUG_NOTE_1,
        )

    def test_note_pages_have_forms(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            URL_ADD,
            URL_EDIT,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.user_client_1.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

    def test_author_can_see_own_notes(self):
        """Пользователь видит свои заметки."""
        response = self.user_client_1.get(URL_LIST)
        self.assertIn('object_list', response.context)
        user_1_notes_in_context = response.context['object_list']
        self.assertEqual(user_1_notes_in_context.count(), 1)
        note = user_1_notes_in_context[0]
        self.assertEqual(note.title, self.note_1.title)
        self.assertEqual(note.text, self.note_1.text)
        self.assertEqual(note.author, self.note_1.author)
        self.assertEqual(note.slug, self.note_1.slug)

    def test_non_author_cannot_see_other_users_notes(self):
        """Пользователь не видит чужие заметки."""
        response = self.user_client_2.get(URL_LIST)
        self.assertIn('object_list', response.context)
        user_2_notes_in_context = response.context['object_list']
        self.assertEqual(user_2_notes_in_context.count(), 0)
