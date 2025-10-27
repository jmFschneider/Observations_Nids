"""Tests pour les vues de transcription."""

from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponse
from django.urls import reverse

from observations.views.view_transcription import is_celery_operational


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    """Désactive le debug_toolbar pour les tests."""
    settings.DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: False}


@pytest.mark.django_db
class TestSelectDirectory:
    """Tests pour la vue de sélection de répertoire."""

    @patch('observations.views.view_transcription.render')
    @patch('os.listdir')
    @patch('os.path.isdir')
    def test_get_affiche_liste_repertoires(self, mock_isdir, mock_listdir, mock_render, authenticated_client):
        """Test que la page GET affiche la liste des répertoires disponibles."""
        # Simuler des répertoires
        mock_listdir.return_value = ['dir1', 'dir2', 'file.txt', 'dir3']
        # Seuls dir1, dir2, dir3 sont des répertoires
        mock_isdir.side_effect = lambda path: not path.endswith('file.txt')

        # Mock render pour éviter le problème de template i18n
        mock_render.return_value = HttpResponse()

        url = reverse('select_directory')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Vérifier que render a été appelé avec les bons arguments
        assert mock_render.called
        call_args = mock_render.call_args
        context = call_args[0][2]
        assert 'directories' in context
        # Devrait contenir 3 répertoires (pas le fichier)
        assert len(context['directories']) == 3

    @patch('observations.views.view_transcription.os.path.isfile')
    @patch('observations.views.view_transcription.os.listdir')
    @patch('observations.views.view_transcription.os.path.isdir')
    def test_post_repertoire_valide(self, mock_isdir, mock_listdir, mock_isfile, authenticated_client):
        """Test de sélection d'un répertoire valide."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ['image1.jpg', 'image2.JPG', 'doc.txt', 'image3.jpeg']
        # Simuler que les fichiers existent sauf doc.txt qui n'est pas une image
        mock_isfile.side_effect = lambda path: not path.endswith('doc.txt')

        url = reverse('select_directory')
        response = authenticated_client.post(url, {'selected_directory': 'test_dir'})

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['file_count'] == 3  # Seulement les .jpg et .jpeg
        assert response_data['directory'] == 'test_dir'

        # Vérifier que le répertoire est stocké en session
        assert authenticated_client.session['processing_directory'] == 'test_dir'

    @patch('os.path.isdir')
    def test_post_repertoire_invalide(self, mock_isdir, authenticated_client):
        """Test de sélection d'un répertoire invalide."""
        mock_isdir.return_value = False

        url = reverse('select_directory')
        response = authenticated_client.post(url, {'selected_directory': 'invalid_dir'})

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is False
        assert 'error' in response_data

    def test_acces_non_authentifie(self, client):
        """Test qu'un utilisateur non authentifié est redirigé."""
        url = reverse('select_directory')
        response = client.get(url)

        assert response.status_code == 302  # Redirection vers login


@pytest.mark.django_db
class TestIsCeleryOperational:
    """Tests pour la fonction is_celery_operational."""

    @patch('observations.views.view_transcription.app.control.ping')
    def test_celery_operational(self, mock_ping):
        """Test quand Celery est opérationnel."""
        mock_ping.return_value = [{'worker1': {'ok': 'pong'}}]

        assert is_celery_operational() is True

    @patch('observations.views.view_transcription.app.control.ping')
    def test_celery_non_operational_no_workers(self, mock_ping):
        """Test quand aucun worker ne répond."""
        mock_ping.return_value = []

        assert is_celery_operational() is False

    @patch('observations.views.view_transcription.app.control.ping')
    def test_celery_exception(self, mock_ping):
        """Test quand une exception est levée."""
        mock_ping.side_effect = Exception("Connection error")

        assert is_celery_operational() is False


@pytest.mark.django_db
class TestProcessImages:
    """Tests pour la vue de traitement des images."""

    def test_sans_repertoire_en_session(self, authenticated_client):
        """Test sans répertoire sélectionné en session."""
        url = reverse('process_images')
        response = authenticated_client.get(url)

        assert response.status_code == 302  # Redirection
        assert response.url == reverse('select_directory')

    @patch('observations.views.view_transcription.is_celery_operational')
    def test_celery_non_operational(self, mock_celery_check, authenticated_client):
        """Test quand Celery n'est pas opérationnel."""
        mock_celery_check.return_value = False

        # Ajouter un répertoire en session
        session = authenticated_client.session
        session['processing_directory'] = 'test_dir'
        session.save()

        url = reverse('process_images')
        response = authenticated_client.get(url)

        assert response.status_code == 302  # Redirection
        assert response.url == reverse('select_directory')

    @patch('observations.views.view_transcription.render')
    @patch('os.makedirs')
    @patch('observations.views.view_transcription.process_images_task.delay')
    @patch('observations.views.view_transcription.is_celery_operational')
    def test_lancement_traitement_succes(self, mock_celery_check, mock_task_delay, mock_makedirs, mock_render, authenticated_client):
        """Test du lancement réussi du traitement."""
        mock_celery_check.return_value = True

        # Simuler une tâche Celery
        mock_task = MagicMock()
        mock_task.id = 'test-task-id-123'
        mock_task_delay.return_value = mock_task

        # Mock render
        mock_render.return_value = HttpResponse()

        # Ajouter un répertoire en session
        session = authenticated_client.session
        session['processing_directory'] = 'test_dir'
        session.save()

        url = reverse('process_images')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Vérifier que render a été appelé avec les bons arguments
        assert mock_render.called
        call_args = mock_render.call_args
        context = call_args[0][2]
        assert 'task_id' in context
        assert context['task_id'] == 'test-task-id-123'

        # Vérifier que le task_id est stocké en session
        assert authenticated_client.session['task_id'] == 'test-task-id-123'


@pytest.mark.django_db
class TestCheckProgress:
    """Tests pour l'endpoint de vérification de progression."""

    def test_sans_task_id(self, authenticated_client):
        """Test sans task_id en session."""
        url = reverse('check_progress')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'NO_TASK'

    @patch('observations.views.view_transcription.AsyncResult')
    def test_etat_pending(self, mock_async_result, authenticated_client):
        """Test avec une tâche en état PENDING."""
        mock_result = MagicMock()
        mock_result.status = 'PENDING'
        mock_result.info = None
        mock_async_result.return_value = mock_result

        session = authenticated_client.session
        session['task_id'] = 'test-task-id'
        session.save()

        url = reverse('check_progress')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'PENDING'
        assert 'message' in response_data

    @patch('observations.views.view_transcription.AsyncResult')
    def test_etat_progress(self, mock_async_result, authenticated_client):
        """Test avec une tâche en cours (PROGRESS)."""
        mock_result = MagicMock()
        mock_result.status = 'PROGRESS'
        mock_result.info = {'total': 10, 'processed': 5, 'message': 'Processing...'}
        mock_async_result.return_value = mock_result

        session = authenticated_client.session
        session['task_id'] = 'test-task-id'
        session.save()

        url = reverse('check_progress')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'PROGRESS'
        assert response_data['percent'] == 50  # 5/10 * 100
        assert response_data['total'] == 10
        assert response_data['processed'] == 5

    @patch('observations.views.view_transcription.AsyncResult')
    def test_etat_success(self, mock_async_result, authenticated_client):
        """Test avec une tâche terminée avec succès."""
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.result = {
            'directory': 'test_dir',
            'duration': 45.5,
            'total': 10,
            'success_count': 8,
            'success_rate': 80.0,
            'results': [{'file': 'test.jpg', 'status': 'success'}]
        }
        mock_async_result.return_value = mock_result

        session = authenticated_client.session
        session['task_id'] = 'test-task-id'
        session['processing_directory'] = 'test_dir'
        session.save()

        url = reverse('check_progress')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'SUCCESS'
        assert response_data['percent'] == 100
        assert response_data['force_redirect'] is True
        assert 'redirect' in response_data

        # Vérifier que les résultats sont stockés en session
        assert 'transcription_results' in authenticated_client.session

    @patch('observations.views.view_transcription.AsyncResult')
    def test_etat_failure(self, mock_async_result, authenticated_client):
        """Test avec une tâche qui a échoué."""
        mock_result = MagicMock()
        mock_result.status = 'FAILURE'
        mock_result.result = Exception("Task failed")
        mock_async_result.return_value = mock_result

        session = authenticated_client.session
        session['task_id'] = 'test-task-id'
        session.save()

        url = reverse('check_progress')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['status'] == 'FAILURE'
        assert response_data['percent'] == 0
        assert 'error' in response_data


@pytest.mark.django_db
class TestTranscriptionResults:
    """Tests pour la vue des résultats de transcription."""

    @patch('observations.views.view_transcription.render')
    def test_avec_resultats_en_session(self, mock_render, authenticated_client):
        """Test avec des résultats stockés en session."""
        session = authenticated_client.session
        session['transcription_results'] = {
            'directory': 'test_dir',
            'total_files': 10,
            'successful_files': 8,
            'results': [
                {'status': 'success', 'json_path': 'result1.json'},
                {'status': 'error', 'error': 'File not found'}
            ]
        }
        session.save()

        # Mock render
        mock_render.return_value = HttpResponse()

        url = reverse('transcription_results')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Vérifier que render a été appelé avec les bons arguments
        assert mock_render.called
        call_args = mock_render.call_args
        context = call_args[0][2]
        assert 'total_files' in context
        assert context['total_files'] == 10

    def test_sans_resultats_avec_task_id(self, authenticated_client):
        """Test sans résultats mais avec une tâche en cours."""
        session = authenticated_client.session
        session['task_id'] = 'test-task-id'
        session.save()

        url = reverse('transcription_results')
        response = authenticated_client.get(url)

        assert response.status_code == 302  # Redirection
        assert response.url == reverse('process_images')

    @patch('observations.views.view_transcription.render')
    def test_sans_resultats_ni_task_id(self, mock_render, authenticated_client):
        """Test sans résultats ni tâche en cours."""
        # Mock render
        mock_render.return_value = HttpResponse()

        url = reverse('transcription_results')
        response = authenticated_client.get(url)

        # Devrait afficher une page vide ou avec un message
        assert response.status_code == 200


@pytest.mark.django_db
class TestStartTranscriptionView:
    """Tests pour l'API de démarrage de transcription."""

    def test_sans_repertoire(self, authenticated_client):
        """Test sans répertoire sélectionné."""
        url = reverse('start_transcription')
        response = authenticated_client.get(url)

        assert response.status_code == 400
        response_data = response.json()
        assert 'error' in response_data

    @patch('observations.views.view_transcription.is_celery_operational')
    def test_celery_non_operational(self, mock_celery_check, authenticated_client):
        """Test quand Celery n'est pas opérationnel."""
        mock_celery_check.return_value = False

        session = authenticated_client.session
        session['processing_directory'] = 'test_dir'
        session.save()

        url = reverse('start_transcription')
        response = authenticated_client.get(url)

        assert response.status_code == 503
        response_data = response.json()
        assert 'error' in response_data
        assert response_data['celery_error'] is True

    @patch('observations.views.view_transcription.process_images_task.delay')
    @patch('observations.views.view_transcription.is_celery_operational')
    def test_demarrage_succes(self, mock_celery_check, mock_task_delay, authenticated_client):
        """Test du démarrage réussi de la transcription."""
        mock_celery_check.return_value = True

        mock_task = MagicMock()
        mock_task.id = 'new-task-id-456'
        mock_task_delay.return_value = mock_task

        session = authenticated_client.session
        session['processing_directory'] = 'test_dir'
        session.save()

        url = reverse('start_transcription')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data['task_id'] == 'new-task-id-456'
        assert 'message' in response_data
        assert 'processing_url' in response_data

        # Vérifier que le task_id est stocké en session
        assert authenticated_client.session['task_id'] == 'new-task-id-456'
