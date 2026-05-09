import 'secure_token_store.dart';
import 'token_store_base.dart';

TokenStore createTokenStore() {
  return SecureTokenStore();
}
