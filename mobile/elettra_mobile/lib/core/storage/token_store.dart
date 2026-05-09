import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'token_store_base.dart';
import 'token_store_factory_stub.dart'
    if (dart.library.html) 'token_store_factory_web.dart'
    if (dart.library.io) 'token_store_factory_secure.dart';

export 'token_store_base.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) {
  return createTokenStore();
});
