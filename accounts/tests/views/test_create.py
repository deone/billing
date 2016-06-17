from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from ...views import create
from ...forms import CreateUserForm
from . import ViewsTests

class IndexTests(ViewsTests):

    def test_create_get(self):
        response = self.c.get(reverse('accounts:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertTemplateUsed(response, 'accounts/create.html')
        self.assertTrue(isinstance(response.context['form'], CreateUserForm))

    def test_index_post(self):
        request = self.factory.post(reverse('accounts:create'),
            data={
              'username': 'b@b.com',
              'password': '12345',
              'first_name': 'Ola',
              'last_name': 'Ade',
              'confirm_password': '12345',
              'country': 'GHA',
              'phone_number': '0542751610'
              })
        request.user = AnonymousUser
        self.session.process_request(request)
        request.session.save()

        response = create(request)

        self.assertTrue(response.status_code, 302)
        self.assertEqual(response.get('location'), reverse('accounts:dashboard'))
