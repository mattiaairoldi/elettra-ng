import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/token_store.dart';
import '../../problems/data/problem_models.dart';
import 'guest_models.dart';

abstract class GuestRepository {
  Future<GuestSessionSummary> startSession();
  Future<GuestSessionSummary> currentOrStartSession();
  Future<GuestDiagnosticResult> sendDiagnosticTurn({
    required String message,
    int? chapterId,
    int? optionId,
    bool useAi = true,
  });
  Future<void> clearSession();
}

class DioGuestRepository implements GuestRepository {
  const DioGuestRepository(this._dio, this._tokenStore);

  final Dio _dio;
  final TokenStore _tokenStore;

  @override
  Future<GuestSessionSummary> startSession() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/guest/sessions',
      options: Options(extra: {'skipAuth': true}),
    );
    final session = GuestSessionSummary.fromJson(response.data ?? const {});
    final token = session.token;
    if (token != null && token.isNotEmpty) {
      await _tokenStore.saveGuestToken(token);
    }
    return session;
  }

  @override
  Future<GuestSessionSummary> currentOrStartSession() async {
    final token = await _tokenStore.readGuestToken();
    if (token == null || token.isEmpty) {
      return startSession();
    }

    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/guest/sessions/current',
        options: Options(
          extra: {'skipAuth': true},
          headers: {'X-Guest-Token': token},
        ),
      );
      return GuestSessionSummary.fromJson(response.data ?? const {});
    } on DioException catch (error) {
      if (error.response?.statusCode == 401 ||
          error.response?.statusCode == 403) {
        await _tokenStore.clearGuestToken();
        return startSession();
      }
      rethrow;
    }
  }

  @override
  Future<GuestDiagnosticResult> sendDiagnosticTurn({
    required String message,
    int? chapterId,
    int? optionId,
    bool useAi = true,
  }) async {
    var token = await _tokenStore.readGuestToken();
    if (token == null || token.isEmpty) {
      final session = await startSession();
      token = session.token;
    }

    final response = await _dio.post<Map<String, dynamic>>(
      '/guest/diagnostic-turns',
      data: {
        'message': message,
        'diagnostic_chapter_id': ?chapterId,
        'diagnostic_chapter_option_id': ?optionId,
        'use_ai': useAi,
      },
      options: Options(
        extra: {'skipAuth': true},
        headers: {'X-Guest-Token': token},
      ),
    );
    final result = GuestDiagnosticResult.fromJson(response.data ?? const {});
    final assistant = await _pollAssistantMessage(
      token,
      result.assistantMessage,
    );
    final snapshot = result.snapshot ?? await _fetchSnapshot(token);
    return GuestDiagnosticResult(
      adviceSteps: result.adviceSteps,
      userMessage: result.userMessage,
      assistantMessage: assistant,
      snapshot: snapshot,
      quotas: result.quotas,
      callToAction: result.callToAction,
    );
  }

  @override
  Future<void> clearSession() async {
    await _tokenStore.clearGuestToken();
  }

  Future<AiMessage?> _pollAssistantMessage(
    String? token,
    AiMessage? message,
  ) async {
    if (token == null || token.isEmpty || message == null) {
      return message;
    }

    var current = message;
    for (var attempt = 0; attempt < 8; attempt += 1) {
      if (current.status == 'completed' || current.status == 'failed') {
        return current;
      }
      await Future<void>.delayed(const Duration(milliseconds: 750));
      final response = await _dio.get<Map<String, dynamic>>(
        '/guest/messages/${current.id}',
        options: Options(
          extra: {'skipAuth': true},
          headers: {'X-Guest-Token': token},
        ),
      );
      current = AiMessage.fromJson(response.data ?? const {});
    }
    return current;
  }

  Future<AiDiagnosticSnapshot?> _fetchSnapshot(String? token) async {
    if (token == null || token.isEmpty) {
      return null;
    }

    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/guest/diagnostic-snapshot',
        options: Options(
          extra: {'skipAuth': true},
          headers: {'X-Guest-Token': token},
        ),
      );
      return AiDiagnosticSnapshot.fromJson(response.data ?? const {});
    } on DioException catch (error) {
      if (error.response?.statusCode == 404) {
        return null;
      }
      rethrow;
    }
  }
}

final guestRepositoryProvider = Provider<GuestRepository>((ref) {
  return DioGuestRepository(
    ref.watch(dioProvider),
    ref.watch(tokenStoreProvider),
  );
});

final guestSessionProvider = FutureProvider.autoDispose<GuestSessionSummary>((
  ref,
) {
  return ref.watch(guestRepositoryProvider).currentOrStartSession();
});
