from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

SLUG_NOTE_UNIQUE = 'slug1'
SLUG_NOTE_EDITED = 'slug_new'

URL_ADD = reverse('notes:add')
URL_EDIT = reverse('notes:edit', args=[SLUG_NOTE_UNIQUE])
URL_DETAIL = reverse('notes:detail', args=[SLUG_NOTE_UNIQUE])
URL_DELETE = reverse('notes:delete', args=[SLUG_NOTE_UNIQUE])
URL_SUCCESS = reverse('notes:success')


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь-Автор-1')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.note_1 = Note.objects.create(
            title='title_1',
            text='text_1',
            author=cls.user,
            slug=SLUG_NOTE_UNIQUE
        )
        cls.title = 'text_1'
        cls.form_data = {
            'text': 'text_2', 'title': 'title_2'
        }

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count_before = Note.objects.count()
        self.client.post(URL_ADD, data=self.form_data)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_before, notes_count_after)

    def test_authorized_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        Note.objects.all().delete()
        self.auth_client.post(URL_ADD, data=self.form_data)
        notes_count = Note.objects.filter(author=self.user).count()
        self.assertEqual(notes_count, 1)
        created_note = Note.objects.latest('id')
        self.assertEqual(created_note.title, self.form_data['title'])
        self.assertEqual(created_note.text, self.form_data['text'])
        self.assertEqual(created_note.author, self.user)

    def test_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        response = self.auth_client.post(
            URL_ADD, data={'slug': SLUG_NOTE_UNIQUE}
        )
        self.assertFormError(
            response, 'form', 'slug', self.note_1.slug + WARNING
        )

    def test_slugify_works(self):
        """
        Если при создании заметки не заполнен slug, то он формируется
        автоматически, с помощью функции pytils.translit.slugify.
        """
        Note.objects.all().delete()
        self.auth_client.post(URL_ADD, data=self.form_data)
        notes_count = Note.objects.filter(author=self.user).count()
        self.assertEqual(notes_count, 1)
        slug_from_form = slugify(self.form_data.pop('title'))[:100]
        created_note = Note.objects.latest('id')
        self.assertEqual(created_note.slug, slug_from_form)


class TestCreatePost(TestCase):
    OLD_NOTE_TEXT = 'OLD TEXT'
    NEW_NOTE_TEXT = 'UPDATED TEXT'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Пользователь-Автор')
        cls.note = Note.objects.create(
            title='title1',
            text=cls.OLD_NOTE_TEXT,
            author=cls.author,
            slug=SLUG_NOTE_UNIQUE,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Пользователь-Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note_url = URL_DETAIL
        cls.edit_url = URL_EDIT
        cls.delete_url = URL_DELETE
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
            'title': 'title_new',
            'slug': SLUG_NOTE_EDITED
        }
        cls.success_url = URL_SUCCESS

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        notes_count_before = Note.objects.filter(author=self.author).count()
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count_after = Note.objects.filter(author=self.author).count()
        self.assertEqual(notes_count_before, notes_count_after + 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалять чужие заметки."""
        notes_count_before = Note.objects.filter(author=self.author).count()
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count_after = Note.objects.filter(author=self.author).count()
        self.assertEqual(notes_count_before, notes_count_after)

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        notes_count_before = Note.objects.filter(author=self.author).count()
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        edited_note = Note.objects.get(id=self.note.id)
        notes_count_after = Note.objects.filter(author=self.author).count()
        self.assertEqual(notes_count_after, notes_count_before)
        self.assertEqual(edited_note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(edited_note.title, self.form_data['title'])
        self.assertEqual(edited_note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать чужие заметки."""
        notes_count_before = Note.objects.filter(author=self.author).count()
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        unedited_note = Note.objects.get(id=self.note.id)
        notes_count_after = Note.objects.filter(author=self.author).count()
        self.assertEqual(notes_count_after, notes_count_before)
        self.assertEqual(unedited_note.text, self.note.text)
        self.assertEqual(unedited_note.title, self.note.title)
        self.assertEqual(unedited_note.slug, self.note.slug)
