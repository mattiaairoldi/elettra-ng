import 'package:web/web.dart' as web;

import '../../features/auth/data/auth_models.dart';
import 'token_store_base.dart';

class WebTokenStore implements TokenStore {
  static const _accessTokenKey = 'auth.access_token';
  static const _refreshTokenKey = 'auth.refresh_token';
  static const _tokenTypeKey = 'auth.token_type';
  static const _accessExpiresInKey = 'auth.access_expires_in';
  static const _refreshExpiresInKey = 'auth.refresh_expires_in';

  AuthTokens? _tokens;

  @override
  Future<AuthTokens?> readTokens() async {
    if (_tokens != null) {
      return _tokens;
    }

    final storage = web.window.localStorage;
    final access = storage.getItem(_accessTokenKey);
    final refresh = storage.getItem(_refreshTokenKey);
    if (access == null || refresh == null) {
      return null;
    }

    _tokens = AuthTokens(
      access: access,
      refresh: refresh,
      tokenType: storage.getItem(_tokenTypeKey) ?? 'Bearer',
      accessExpiresIn: int.tryParse(storage.getItem(_accessExpiresInKey) ?? '') ?? 0,
      refreshExpiresIn: int.tryParse(storage.getItem(_refreshExpiresInKey) ?? '') ?? 0,
    );
    return _tokens;
  }

  @override
  Future<String?> readAccessToken() async {
    return _tokens?.access ?? web.window.localStorage.getItem(_accessTokenKey);
  }

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    _tokens = tokens;
    final storage = web.window.localStorage;
    storage.setItem(_accessTokenKey, tokens.access);
    storage.setItem(_refreshTokenKey, tokens.refresh);
    storage.setItem(_tokenTypeKey, tokens.tokenType);
    storage.setItem(_accessExpiresInKey, tokens.accessExpiresIn.toString());
    storage.setItem(_refreshExpiresInKey, tokens.refreshExpiresIn.toString());
  }

  @override
  Future<void> clearTokens() async {
    _tokens = null;
    final storage = web.window.localStorage;
    storage.removeItem(_accessTokenKey);
    storage.removeItem(_refreshTokenKey);
    storage.removeItem(_tokenTypeKey);
    storage.removeItem(_accessExpiresInKey);
    storage.removeItem(_refreshExpiresInKey);
  }
}
