import '../../features/auth/data/auth_models.dart';

abstract class TokenStore {
  Future<AuthTokens?> readTokens();
  Future<String?> readAccessToken();
  Future<void> saveTokens(AuthTokens tokens);
  Future<void> clearTokens();
}
