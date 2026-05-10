import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import 'problem_models.dart';

abstract class ProblemsRepository {
  Future<List<CustomerProblem>> fetchProblems();
  Future<CustomerProblem> fetchProblem(int problemId);
  Future<CustomerProblem> createProblemFromDiagnosis({
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  });
  Future<List<DiagnosticChapter>> fetchDiagnosticChapters({int? categoryId});
  Future<List<DiagnosticAdviceStep>> fetchAdviceSteps({
    required int chapterId,
    int? optionId,
  });
  Future<DiagnosticFeedbackResult> sendAdviceFeedback({
    required int stepId,
    required int caseId,
    required bool resolved,
    required String note,
  });
  Future<AiSessionSummary> createAiSession({required int caseId});
  Future<List<AiMessage>> fetchAiMessages(int sessionId);
  Future<DiagnosticTurnResult> sendDiagnosticTurn({
    required int sessionId,
    required String content,
    int? chapterId,
    int? optionId,
  });
  Future<List<ProfessionalProfileSummary>> fetchProfessionals({
    int? categoryId,
  });
  Future<CaseShareRequestSummary> shareCase({
    required int caseId,
    required ProfessionalProfileSummary professional,
    required String title,
    required String summary,
  });
}

class DioProblemsRepository implements ProblemsRepository {
  const DioProblemsRepository(this._dio);

  final Dio _dio;

  @override
  Future<List<CustomerProblem>> fetchProblems() async {
    final response = await _dio.get<List<dynamic>>('/cases');
    final data = response.data ?? const [];
    return data
        .map((item) => CustomerProblem.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<CustomerProblem> fetchProblem(int problemId) async {
    final response = await _dio.get<Map<String, dynamic>>('/cases/$problemId');
    return CustomerProblem.fromJson(response.data ?? const {});
  }

  @override
  Future<CustomerProblem> createProblemFromDiagnosis({
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/cases',
      data: {
        'category_id': categoryId,
        'title': title,
        'description': description,
        'priority': priority,
      },
    );
    return CustomerProblem.fromJson(response.data ?? const {});
  }

  @override
  Future<List<DiagnosticChapter>> fetchDiagnosticChapters({
    int? categoryId,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/diagnostic-chapters',
      queryParameters: {
        if (categoryId != null && categoryId > 0) 'category_id': categoryId,
      },
      options: Options(extra: {'skipAuth': true}),
    );
    final data = response.data ?? const [];
    return data
        .map((item) => DiagnosticChapter.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<List<DiagnosticAdviceStep>> fetchAdviceSteps({
    required int chapterId,
    int? optionId,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/diagnostic-chapters/$chapterId/advice-steps',
      queryParameters: {'option_id': ?optionId},
      options: Options(extra: {'skipAuth': true}),
    );
    final data = response.data ?? const [];
    return data
        .map(
          (item) => DiagnosticAdviceStep.fromJson(item as Map<String, dynamic>),
        )
        .toList();
  }

  @override
  Future<DiagnosticFeedbackResult> sendAdviceFeedback({
    required int stepId,
    required int caseId,
    required bool resolved,
    required String note,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/diagnostic-advice-steps/$stepId/feedback',
      data: {
        'case_id': caseId,
        'resolved': resolved,
        if (note.trim().isNotEmpty) 'note': note.trim(),
      },
    );
    return DiagnosticFeedbackResult.fromJson(response.data ?? const {});
  }

  @override
  Future<AiSessionSummary> createAiSession({required int caseId}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/ai/sessions',
      data: {'case_id': caseId},
    );
    return AiSessionSummary.fromJson(response.data ?? const {});
  }

  @override
  Future<List<AiMessage>> fetchAiMessages(int sessionId) async {
    final response = await _dio.get<List<dynamic>>(
      '/ai/sessions/$sessionId/messages',
    );
    final data = response.data ?? const [];
    return data
        .map((item) => AiMessage.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<DiagnosticTurnResult> sendDiagnosticTurn({
    required int sessionId,
    required String content,
    int? chapterId,
    int? optionId,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/ai/sessions/$sessionId/diagnostic-turns',
      data: {
        'content': content,
        'diagnostic_chapter_id': ?chapterId,
        'diagnostic_chapter_option_id': ?optionId,
      },
    );
    final payload = response.data ?? const {};
    final userMessage = AiMessage.fromJson(
      payload['user_message'] as Map<String, dynamic>,
    );
    var assistantMessage = AiMessage.fromJson(
      payload['assistant_message'] as Map<String, dynamic>,
    );
    var snapshot = _parseSnapshot(payload['diagnostic_snapshot']);

    for (var attempt = 0; attempt < 8; attempt += 1) {
      if (assistantMessage.status == 'completed' ||
          assistantMessage.status == 'failed') {
        break;
      }
      await Future<void>.delayed(const Duration(milliseconds: 750));
      final messageResponse = await _dio.get<Map<String, dynamic>>(
        '/ai/sessions/$sessionId/messages/${assistantMessage.id}',
      );
      assistantMessage = AiMessage.fromJson(messageResponse.data ?? const {});
    }

    if (snapshot == null) {
      try {
        final snapshotResponse = await _dio.get<Map<String, dynamic>>(
          '/ai/sessions/$sessionId/diagnostic-snapshot',
        );
        snapshot = AiDiagnosticSnapshot.fromJson(
          snapshotResponse.data ?? const {},
        );
      } on DioException catch (error) {
        if (error.response?.statusCode != 404) {
          rethrow;
        }
      }
    }

    return DiagnosticTurnResult(
      userMessage: userMessage,
      assistantMessage: assistantMessage,
      snapshot: snapshot,
    );
  }

  @override
  Future<List<ProfessionalProfileSummary>> fetchProfessionals({
    int? categoryId,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/professionals',
      queryParameters: {
        if (categoryId != null && categoryId > 0) 'category_id': categoryId,
      },
      options: Options(extra: {'skipAuth': true}),
    );
    final data = response.data ?? const [];
    return data
        .map(
          (item) =>
              ProfessionalProfileSummary.fromJson(item as Map<String, dynamic>),
        )
        .where((item) => item.recipientOrganizationId != null)
        .toList();
  }

  @override
  Future<CaseShareRequestSummary> shareCase({
    required int caseId,
    required ProfessionalProfileSummary professional,
    required String title,
    required String summary,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/cases/$caseId/share-requests',
      data: {
        'recipient_organization_id': professional.recipientOrganizationId,
        if (professional.recipientMembershipId != null)
          'recipient_membership_id': professional.recipientMembershipId,
        'share_scope': 'summary',
        'visible_title': title,
        'visible_summary': summary,
        'shared_payload_json': {
          'source': 'flutter_mobile',
          'professional_profile_id': professional.id,
        },
      },
    );
    return CaseShareRequestSummary.fromJson(response.data ?? const {});
  }

  AiDiagnosticSnapshot? _parseSnapshot(Object? value) {
    if (value is Map<String, dynamic>) {
      return AiDiagnosticSnapshot.fromJson(value);
    }
    return null;
  }
}

final problemsRepositoryProvider = Provider<ProblemsRepository>((ref) {
  return DioProblemsRepository(ref.watch(dioProvider));
});

final problemsProvider = FutureProvider.autoDispose<List<CustomerProblem>>((
  ref,
) {
  return ref.watch(problemsRepositoryProvider).fetchProblems();
});

final diagnosticChaptersProvider = FutureProvider.autoDispose
    .family<List<DiagnosticChapter>, int?>((ref, categoryId) {
      return ref
          .watch(problemsRepositoryProvider)
          .fetchDiagnosticChapters(categoryId: categoryId);
    });

final professionalsProvider = FutureProvider.autoDispose
    .family<List<ProfessionalProfileSummary>, int?>((ref, categoryId) {
      return ref
          .watch(problemsRepositoryProvider)
          .fetchProfessionals(categoryId: categoryId);
    });
