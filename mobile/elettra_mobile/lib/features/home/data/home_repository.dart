import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import 'home_models.dart';

abstract class HomeRepository {
  Future<HomeOverview> fetchOverview();
  Future<void> createProperty({
    required String name,
    required String addressText,
    required String city,
    required String notes,
  });
  Future<void> createAsset({
    required int propertyId,
    required int categoryId,
    required String name,
    required String description,
    required String locationText,
    required Map<String, dynamic> metadata,
  });
  Future<void> createMaintenanceEvent({
    required int assetId,
    required String eventType,
    required String title,
    required String description,
    required DateTime eventDate,
  });
  Future<void> createMaintenanceReminder({
    required int assetId,
    required String title,
    required String description,
    required DateTime dueAt,
    required String recurrenceRule,
  });
  Future<void> completeReminder(int reminderId);
  Future<void> uploadAssetAttachment({
    required int assetId,
    required String fileName,
    required Uint8List bytes,
    required String attachmentType,
  });
  Future<int> createProblemFromAsset({
    required int assetId,
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  });
}

class DioHomeRepository implements HomeRepository {
  const DioHomeRepository(this._dio);

  final Dio _dio;

  @override
  Future<HomeOverview> fetchOverview() async {
    final responses = await Future.wait([
      _dio.get<List<dynamic>>('/properties'),
      _dio.get<List<dynamic>>('/assets'),
      _dio.get<List<dynamic>>('/categories'),
      _dio.get<List<dynamic>>('/asset-maintenance-events'),
      _dio.get<List<dynamic>>('/asset-maintenance-reminders'),
      _dio.get<List<dynamic>>('/attachments'),
    ]);

    final properties = (responses[0].data ?? const [])
        .map((item) => HomeProperty.fromJson(item as Map<String, dynamic>))
        .toList();
    final assets = (responses[1].data ?? const [])
        .map((item) => HomeAsset.fromJson(item as Map<String, dynamic>))
        .toList();
    final categories = (responses[2].data ?? const [])
        .map((item) => HomeCategory.fromJson(item as Map<String, dynamic>))
        .toList();
    final events = (responses[3].data ?? const [])
        .map(
          (item) => HomeMaintenanceEvent.fromJson(item as Map<String, dynamic>),
        )
        .toList();
    final reminders = (responses[4].data ?? const [])
        .map(
          (item) =>
              HomeMaintenanceReminder.fromJson(item as Map<String, dynamic>),
        )
        .toList();
    final attachments = (responses[5].data ?? const [])
        .map((item) => HomeAttachment.fromJson(item as Map<String, dynamic>))
        .toList();

    return HomeOverview(
      properties: properties,
      assets: assets,
      categories: categories,
      eventsByAssetId: _groupByAssetId(events, (event) => event.assetId),
      remindersByAssetId: _groupByAssetId(
        reminders,
        (reminder) => reminder.assetId,
      ),
      attachmentsByAssetId: _groupByAssetId(
        attachments,
        (attachment) => attachment.assetId,
      ),
    );
  }

  @override
  Future<void> createProperty({
    required String name,
    required String addressText,
    required String city,
    required String notes,
  }) async {
    await _dio.post<void>(
      '/properties',
      data: {
        'name': name,
        'address_text': addressText,
        'city': city,
        'notes': notes,
      },
    );
  }

  @override
  Future<void> createAsset({
    required int propertyId,
    required int categoryId,
    required String name,
    required String description,
    required String locationText,
    required Map<String, dynamic> metadata,
  }) async {
    await _dio.post<void>(
      '/assets',
      data: {
        'property_id': propertyId,
        'category_id': categoryId,
        'name': name,
        'description': description,
        'location_text': locationText,
        'metadata_json': metadata,
      },
    );
  }

  @override
  Future<void> createMaintenanceEvent({
    required int assetId,
    required String eventType,
    required String title,
    required String description,
    required DateTime eventDate,
  }) async {
    await _dio.post<void>(
      '/asset-maintenance-events',
      data: {
        'asset_id': assetId,
        'event_type': eventType,
        'title': title,
        'description': description,
        'event_date': _dateOnly(eventDate),
      },
    );
  }

  @override
  Future<void> createMaintenanceReminder({
    required int assetId,
    required String title,
    required String description,
    required DateTime dueAt,
    required String recurrenceRule,
  }) async {
    await _dio.post<void>(
      '/asset-maintenance-reminders',
      data: {
        'asset_id': assetId,
        'title': title,
        'description': description,
        'due_at': dueAt.toIso8601String(),
        'recurrence_rule': recurrenceRule,
      },
    );
  }

  @override
  Future<void> completeReminder(int reminderId) async {
    await _dio.post<void>('/asset-maintenance-reminders/$reminderId/complete');
  }

  @override
  Future<void> uploadAssetAttachment({
    required int assetId,
    required String fileName,
    required Uint8List bytes,
    required String attachmentType,
  }) async {
    await _dio.post<void>(
      '/attachments',
      data: FormData.fromMap({
        'asset_id': assetId,
        'attachment_type': attachmentType,
        'file': MultipartFile.fromBytes(bytes, filename: fileName),
      }),
    );
  }

  @override
  Future<int> createProblemFromAsset({
    required int assetId,
    required int categoryId,
    required String title,
    required String description,
    required String priority,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/cases',
      data: {
        'asset_id': assetId,
        'category_id': categoryId,
        'title': title,
        'description': description,
        'priority': priority,
      },
    );
    return response.data?['id'] as int;
  }

  Map<int, List<T>> _groupByAssetId<T>(
    List<T> items,
    int? Function(T item) assetIdOf,
  ) {
    final grouped = <int, List<T>>{};
    for (final item in items) {
      final assetId = assetIdOf(item);
      if (assetId == null) {
        continue;
      }
      grouped.putIfAbsent(assetId, () => []).add(item);
    }
    return grouped;
  }

  String _dateOnly(DateTime value) {
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');
    return '${value.year}-$month-$day';
  }
}

final homeRepositoryProvider = Provider<HomeRepository>((ref) {
  return DioHomeRepository(ref.watch(dioProvider));
});

final homeOverviewProvider = FutureProvider.autoDispose<HomeOverview>((ref) {
  return ref.watch(homeRepositoryProvider).fetchOverview();
});
