import '../../features/auth/data/auth_models.dart';
import 'token_store_base.dart';

class InMemoryTokenStore implements TokenStore {
  AuthTokens? _tokens;
  String? _guestToken;

  @override
  Future<AuthTokens?> readTokens() async => _tokens;

  @override
  Future<String?> readAccessToken() async => _tokens?.access;

  @override
  Future<void> saveTokens(AuthTokens tokens) async {
    _tokens = tokens;
  }

  @override
  Future<void> clearTokens() async {
    _tokens = null;
  }

  @override
  Future<String?> readGuestToken() async => _guestToken;

  @override
  Future<void> saveGuestToken(String token) async {
    _guestToken = token;
  }

  @override
  Future<void> clearGuestToken() async {
    _guestToken = null;
  }
}
