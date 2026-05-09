import 'token_store_base.dart';
import 'web_token_store.dart';

TokenStore createTokenStore() {
  return WebTokenStore();
}
