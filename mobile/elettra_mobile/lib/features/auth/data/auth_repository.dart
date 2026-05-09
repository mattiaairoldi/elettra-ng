import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/token_store.dart';
import 'auth_models.dart';

abstract class AuthRepository {
  Future<LoginResult> login({required String email, required String password});
  Future<AppUser> currentUser();
  Future<void> logout(String refreshToken);
}

class DioAuthRepository implements AuthRepository {
  const DioAuthRepository(this._dio);

  final Dio _dio;

  @override
  Future<LoginResult> login({required String email, required String password}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/auth/token/login',
      data: {
        'email': email,
        'password': password,
      },
      options: Options(extra: {'skipAuth': true}),
    );
    return LoginResult.fromJson(response.data ?? const {});
  }

  @override
  Future<AppUser> currentUser() async {
    final response = await _dio.get<Map<String, dynamic>>('/auth/me');
    final data = response.data ?? const {};
    return AppUser.fromJson(data['user'] as Map<String, dynamic>);
  }

  @override
  Future<void> logout(String refreshToken) async {
    await _dio.post<void>(
      '/auth/token/logout',
      data: {'refresh': refreshToken},
    );
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return DioAuthRepository(ref.watch(dioProvider));
});

class AuthSessionNotifier extends Notifier<AuthSession?> {
  @override
  AuthSession? build() => null;

  void setSession(AuthSession? session) {
    state = session;
  }
}

final authSessionProvider = NotifierProvider<AuthSessionNotifier, AuthSession?>(
  AuthSessionNotifier.new,
);

final authBootstrapProvider = FutureProvider<void>((ref) async {
  if (ref.read(authSessionProvider) != null) {
    return;
  }

  final tokenStore = ref.watch(tokenStoreProvider);
  final tokens = await tokenStore.readTokens();
  if (tokens == null) {
    return;
  }

  try {
    final user = await ref.watch(authRepositoryProvider).currentUser();
    ref.read(authSessionProvider.notifier).setSession(
          AuthSession(user: user, tokens: tokens),
        );
  } catch (_) {
    await tokenStore.clearTokens();
    ref.read(authSessionProvider.notifier).setSession(null);
  }
});

class AuthActions {
  const AuthActions(this._ref);

  final Ref _ref;

  Future<void> login({required String email, required String password}) async {
    final result = await _ref.read(authRepositoryProvider).login(
          email: email,
          password: password,
        );
    await _ref.read(tokenStoreProvider).saveTokens(result.tokens);
    _ref.read(authSessionProvider.notifier).setSession(AuthSession(
          user: result.user,
          tokens: result.tokens,
        ));
  }

  Future<void> logout() async {
    final session = _ref.read(authSessionProvider);
    if (session != null) {
      try {
        await _ref.read(authRepositoryProvider).logout(session.tokens.refresh);
      } catch (_) {
        // Local logout must still work if the token is already expired/revoked.
      }
    }
    await _ref.read(tokenStoreProvider).clearTokens();
    _ref.read(authSessionProvider.notifier).setSession(null);
  }
}

final authActionsProvider = Provider<AuthActions>((ref) {
  return AuthActions(ref);
});
