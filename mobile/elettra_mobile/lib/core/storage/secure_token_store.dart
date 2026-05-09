import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../features/auth/data/auth_models.dart';
import 'token_store_base.dart';

class SecureTokenStore implements TokenStore {
  SecureTokenStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'auth.access_token';
  static const _refreshTokenKey = 'auth.refresh_token';
  static const _tokenTypeKey = 'auth.token_type';
  static const _accessExpiresInKey = 'auth.access_expires_in';
  static const _refreshExpiresInKey = 'auth.refresh_expires_in';

  final FlutterSecureStorage _storage;
  AuthTokens? _tokens;

  @override
  Future<AuthTokens?> readTokens() async {
    if (_tokens != null) {
      return _tokens;
    }

    final access = await _storage.read(key: _accessTokenKey);
    final refresh = await _storage.read(key: _refreshTokenKey);
    if (access == null || refresh == null) {
      return null;
    }

    _tokens = AuthTokens(
      access: access,
      refresh: refresh,
      tokenType: await _storage.read(key: _tokenTypeKey) ?? 'Bearer',
      accessExpiresIn: int.tryParse(await _storage.read(key: _accessExpiresInKey) ?? '') ?? 0,
      refreshExpiresIn: int.tryParse(await _storage.read(key: _refreshExpiresInKey) ?? '') ?? 0,
    );
    return _tokens;
  }

  @override
  Future<String?> readAccessToken() async {
    return _tokens?.access ?? _storage.read(key: _accessTokenKey);
  }

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    _tokens = tokens;
    await Future.wait([
      _storage.write(key: _accessTokenKey, value: tokens.access),
      _storage.write(key: _refreshTokenKey, value: tokens.refresh),
      _storage.write(key: _tokenTypeKey, value: tokens.tokenType),
      _storage.write(key: _accessExpiresInKey, value: tokens.accessExpiresIn.toString()),
      _storage.write(key: _refreshExpiresInKey, value: tokens.refreshExpiresIn.toString()),
    ]);
  }

  @override
  Future<void> clearTokens() async {
    _tokens = null;
    await Future.wait([
      _storage.delete(key: _accessTokenKey),
      _storage.delete(key: _refreshTokenKey),
      _storage.delete(key: _tokenTypeKey),
      _storage.delete(key: _accessExpiresInKey),
      _storage.delete(key: _refreshExpiresInKey),
    ]);
  }
}
