import threading
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from engine.repository import Repository
from services.api import audience


@pytest.fixture
def context(tmp_path):
    repo = Repository(tmp_path / 'audience.db')
    repo.save_session({'id': 's1', 'execution': 'template'})
    stories = [{'id': 'story-pass-1', 'family': 'pass', 'title': 'A pass', 'status': 'ready',
                'revision': 1, 'package_hash': 'a' * 64, 'queue_state': 'live',
                'eligible_from_ms': 100, 'expires_at_ms': 1000}]
    def require(token):
        if token != 'key':
            raise HTTPException(401, detail={'code': 'producer_auth_required'})
    def session(sid):
        result = repo.get_session(sid)
        if not result:
            raise HTTPException(404)
        return result
    app = FastAPI()
    app.include_router(audience.create_audience_router(lambda: repo, require, session, threading.RLock(),
                        lambda sid, producer: {'stories': stories, 'clock_ms': 500}, lambda s: s['execution'] == 'ai'))
    return TestClient(app), repo, stories


def path(suffix=''):
    return '/api/replay-sessions/s1/audience' + suffix


def headers():
    return {'X-Producer-Token': 'key'}


def test_rehearsal_counts_participants_is_protected_and_suggests_without_confirmation(context):
    client, repo, _ = context
    assert client.get(path()).status_code == 401
    assert client.get(path(), headers=headers()).json()['groups'] == []
    response = client.post(path('/rehearsal'), headers=headers(), json={'messages': [
        {'text': '¿Qué pasó en el pase?', 'author_id': 'one'},
        {'text': '¿Qué pasó en el pase?', 'author_id': 'one'},
        {'text': '¿Qué pasó en el pase?', 'author_id': 'two'},
    ]})
    assert response.status_code == 200
    data = response.json()
    group = data['groups'][0]
    assert data['source'] == 'rehearsal'
    assert group['message_count'] == 3 and group['participant_count'] == 2
    assert group['story_id'] == 'story-pass-1' and not group['association_confirmed']
    assert group['mode'] == 'template'
    assert 'messages' not in data
    assert 'one' not in str(repo.get_session('s1')['audience']['messages'])


def test_manual_association_requires_current_exact_revision_and_stales_on_change(context):
    client, _, stories = context
    result = client.post(path('/rehearsal'), headers=headers(), json={'messages': [
        {'text': '¿Qué pasó en el pase?', 'author_id': 'one'}]}).json()
    group_id = result['groups'][0]['id']
    request = {'story_id': 'story-pass-1', 'expected_revision': 1, 'package_hash': 'a' * 64}
    assert client.post(path(f'/groups/{group_id}/associate'), headers=headers(),
                       json={**request, 'package_hash': 'b' * 64}).status_code == 409
    result = client.post(path(f'/groups/{group_id}/associate'), headers=headers(), json=request).json()
    assert result['groups'][0]['association_confirmed'] is True
    stories[0]['revision'] = 2
    stories[0]['package_hash'] = 'b' * 64
    assert client.get(path(), headers=headers()).json()['groups'][0]['association_confirmed'] is False


def test_unrelated_questions_and_ambiguous_moments_are_not_combined_or_associated(context):
    client, _, stories = context
    stories.append({**stories[0], 'id': 'story-pass-2'})
    data = client.post(path('/rehearsal'), headers=headers(), json={'messages': [
        {'text': '¿Quién dio el pase?', 'author_id': 'one'},
        {'text': '¿Qué distancia tuvo el pase?', 'author_id': 'two'},
    ]}).json()
    assert len(data['groups']) == 2
    assert all(g['story_id'] is None and not g['association_confirmed'] for g in data['groups'])


def test_future_story_cannot_be_associated(context):
    client, _, stories = context
    stories[0]['eligible_from_ms'] = 501
    data = client.post(path('/rehearsal'), headers=headers(), json={'messages': [
        {'text': '¿Qué pasó en el pase?', 'author_id': 'one'}]}).json()
    group = data['groups'][0]
    assert group['story_id'] is None
    response = client.post(path('/groups/' + group['id'] + '/associate'), headers=headers(), json={
        'story_id': 'story-pass-1', 'expected_revision': 1, 'package_hash': 'a' * 64})
    assert response.status_code == 409


def test_real_youtube_path_pages_and_honors_poll_interval(context, monkeypatch):
    client, _, _ = context
    monkeypatch.setenv('YOUTUBE_CLIENT_ID', 'test-client')
    monkeypatch.setenv('YOUTUBE_CLIENT_SECRET', 'test-secret')
    class OAuthResponse:
        status_code = 200
        def json(self):
            return {'access_token': 'server-access-token', 'refresh_token': 'server-refresh-token',
                    'expires_in': 3600, 'scope': 'https://www.googleapis.com/auth/youtube.readonly'}
    class OAuthClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): return OAuthResponse()
    monkeypatch.setattr(audience.httpx, 'AsyncClient', lambda **kwargs: OAuthClient())
    start = client.post(path('/oauth/start'), headers=headers())
    assert start.status_code == 200
    from urllib.parse import parse_qs, urlparse
    state = parse_qs(urlparse(start.json()['authorization_url']).query)['state'][0]
    callback = client.get('/api/youtube/oauth/callback', params={'code': 'auth-code', 'state': state}, follow_redirects=False)
    assert callback.status_code == 303 and 'youtube_oauth=connected' in callback.headers['location']
    assert client.get(path(), headers=headers()).json()['youtube_authorized'] is True
    calls = []
    async def get(endpoint, params, token):
        calls.append((endpoint, params, token))
        if endpoint == 'videos':
            return {'items': [{'liveStreamingDetails': {'activeLiveChatId': 'chat-1'}}]}
        return {'items': [{'id': 'message-1', 'authorDetails': {'channelId': 'channel'},
                           'snippet': {'publishedAt': datetime.now(timezone.utc).isoformat(),
                                       'textMessageDetails': {'messageText': 'What was that pass?'}}}],
                'nextPageToken': 'continuation', 'pollingIntervalMillis': 5000}
    monkeypatch.setattr(audience, '_youtube_get', get)
    assert client.post(path('/connect'), headers=headers(), json={'video_id': 'abc123def45'}).status_code == 200
    data = client.post(path('/refresh'), headers=headers()).json()
    assert data['source'] == 'youtube' and data['groups'][0]['mode'] == 'template'
    assert client.post(path('/refresh'), headers=headers()).status_code == 200
    assert len(calls) == 2
    assert all(call[2] == 'server-access-token' for call in calls)


def test_youtube_live_requires_oauth_and_oauth_state_is_single_use(context, monkeypatch):
    client, _, _ = context
    monkeypatch.delenv('YOUTUBE_CLIENT_ID', raising=False)
    monkeypatch.delenv('YOUTUBE_CLIENT_SECRET', raising=False)
    assert client.post(path('/oauth/start'), headers=headers()).status_code == 503
    assert client.post(path('/connect'), headers=headers(), json={'video_id': 'abc123def45'}).status_code == 409
    monkeypatch.setenv('YOUTUBE_CLIENT_ID', 'test-client')
    monkeypatch.setenv('YOUTUBE_CLIENT_SECRET', 'test-secret')
    start = client.post(path('/oauth/start'), headers=headers()).json()
    from urllib.parse import parse_qs, urlparse
    state = parse_qs(urlparse(start['authorization_url']).query)['state'][0]
    assert client.get('/api/youtube/oauth/callback', params={'code': 'code', 'state': 'invalid'},
                      follow_redirects=False).status_code == 400
    assert client.get('/api/youtube/oauth/callback', params={'error': 'access_denied', 'state': state},
                      follow_redirects=False).status_code == 303
    assert client.get('/api/youtube/oauth/callback', params={'code': 'code', 'state': state},
                      follow_redirects=False).status_code == 400


def test_ai_role_is_real_and_fallback_is_labeled(context, monkeypatch):
    client, repo, _ = context
    session = repo.get_session('s1'); session['execution'] = 'ai'; repo.save_session(session)
    roles = []
    class Provider:
        async def complete(self, role, instruction, payload, schema, max_tokens):
            roles.append(role)
            return {'groups': [{'indices': [0, 1], 'story_id': 'story-pass-1',
                                'interpretation': 'Viewers want to understand what changed after the pass.',
                                'reason': 'Similar questions.'}]}, {}
        async def close(self): pass
    monkeypatch.setattr(audience, 'AgentFrameworkProvider', Provider)
    body = {'messages': [{'text': '¿Qué pasó en el pase?', 'author_id': 'one'},
                         {'text': 'Explain that pass', 'author_id': 'two'}]}
    data = client.post(path('/rehearsal'), headers=headers(), json=body).json()
    assert roles == ['Audience Agent'] and data['groups'][0]['mode'] == 'ai'
    assert data['groups'][0]['participant_count'] == 2
    assert data['groups'][0]['interpretation'] == 'Viewers want to understand what changed after the pass.'
    class FailedProvider(Provider):
        async def complete(self, *args): raise RuntimeError('secret provider error')
    monkeypatch.setattr(audience, 'AgentFrameworkProvider', FailedProvider)
    data = client.post(path('/rehearsal'), headers=headers(), json={'messages': [body['messages'][0]]}).json()
    assert all(g['mode'] == 'fallback' for g in data['groups'])
    assert 'secret provider error' not in str(data)
