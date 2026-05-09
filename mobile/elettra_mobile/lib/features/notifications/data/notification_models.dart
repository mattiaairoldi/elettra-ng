class AppNotification {
  const AppNotification({
    required this.id,
    required this.recipientUserId,
    required this.actorUserId,
    required this.type,
    required this.title,
    required this.body,
    required this.priority,
    required this.targetType,
    required this.targetId,
    required this.deepLink,
    required this.metadata,
    required this.isRead,
    required this.readAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as int,
      recipientUserId: json['recipient_user_id'] as int? ?? 0,
      actorUserId: json['actor_user_id'] as int?,
      type: json['notification_type']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      priority: json['priority']?.toString() ?? 'normal',
      targetType: json['target_type']?.toString() ?? '',
      targetId: json['target_id']?.toString() ?? '',
      deepLink: json['deep_link']?.toString() ?? '',
      metadata: _metadataMap(json['metadata_json']),
      isRead: json['is_read'] as bool? ?? false,
      readAt: DateTime.tryParse(json['read_at']?.toString() ?? ''),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  final int id;
  final int recipientUserId;
  final int? actorUserId;
  final String type;
  final String title;
  final String body;
  final String priority;
  final String targetType;
  final String targetId;
  final String deepLink;
  final Map<String, dynamic> metadata;
  final bool isRead;
  final DateTime? readAt;
  final DateTime? createdAt;
  final DateTime? updatedAt;
}

class NotificationSummary {
  const NotificationSummary({required this.unreadCount});

  factory NotificationSummary.fromJson(Map<String, dynamic> json) {
    return NotificationSummary(unreadCount: json['unread_count'] as int? ?? 0);
  }

  final int unreadCount;
}

Map<String, dynamic> _metadataMap(Object? value) {
  if (value is Map) {
    return Map.unmodifiable(
      value.map((key, item) => MapEntry(key.toString(), item)),
    );
  }
  return const {};
}
