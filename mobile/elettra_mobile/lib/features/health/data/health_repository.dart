import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

class HealthStatus {
  const HealthStatus({required this.status});

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(status: json['status']?.toString() ?? 'unknown');
  }

  final String status;

  bool get isOk => status == 'ok';
}

abstract class HealthRepository {
  Future<HealthStatus> fetchHealth();
}

class DioHealthRepository implements HealthRepository {
  const DioHealthRepository(this._dio);

  final Dio _dio;

  @override
  Future<HealthStatus> fetchHealth() async {
    final response = await _dio.get<Map<String, dynamic>>('/health');
    return HealthStatus.fromJson(response.data ?? const {});
  }
}

final healthRepositoryProvider = Provider<HealthRepository>((ref) {
  return DioHealthRepository(ref.watch(dioProvider));
});

final healthStatusProvider = FutureProvider<HealthStatus>((ref) {
  return ref.watch(healthRepositoryProvider).fetchHealth();
});
