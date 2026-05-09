import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import 'notification_models.dart';

abstract class NotificationsRepository {
  Future<List<AppNotification>> fetchNotifications({bool unreadOnly = false});
  Future<NotificationSummary> fetchSummary();
  Future<AppNotification> markRead(int notificationId);
  Future<int> markAllRead();
}

class DioNotificationsRepository implements NotificationsRepository {
  const DioNotificationsRepository(this._dio);

  final Dio _dio;

  @override
  Future<List<AppNotification>> fetchNotifications({
    bool unreadOnly = false,
  }) async {
    final response = await _dio.get<List<dynamic>>(
      '/notifications',
      queryParameters: {if (unreadOnly) 'unread': 'true'},
    );
    final data = response.data ?? const [];
    return data
        .map((item) => AppNotification.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<NotificationSummary> fetchSummary() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/notifications/summary',
    );
    return NotificationSummary.fromJson(response.data ?? const {});
  }

  @override
  Future<AppNotification> markRead(int notificationId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/notifications/$notificationId/read',
    );
    final payload = response.data ?? const {};
    return AppNotification.fromJson(
      payload['notification'] as Map<String, dynamic>,
    );
  }

  @override
  Future<int> markAllRead() async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/notifications/mark-all-read',
    );
    return response.data?['updated_count'] as int? ?? 0;
  }
}

final notificationsRepositoryProvider = Provider<NotificationsRepository>((
  ref,
) {
  return DioNotificationsRepository(ref.watch(dioProvider));
});

final notificationsProvider = FutureProvider.autoDispose<List<AppNotification>>(
  (ref) {
    return ref.watch(notificationsRepositoryProvider).fetchNotifications();
  },
);

final notificationSummaryProvider =
    FutureProvider.autoDispose<NotificationSummary>((ref) {
      return ref.watch(notificationsRepositoryProvider).fetchSummary();
    });
