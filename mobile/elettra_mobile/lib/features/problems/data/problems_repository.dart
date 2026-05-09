import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import 'problem_models.dart';

abstract class ProblemsRepository {
  Future<List<CustomerProblem>> fetchProblems();
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
}

final problemsRepositoryProvider = Provider<ProblemsRepository>((ref) {
  return DioProblemsRepository(ref.watch(dioProvider));
});

final problemsProvider = FutureProvider.autoDispose<List<CustomerProblem>>((ref) {
  return ref.watch(problemsRepositoryProvider).fetchProblems();
});
