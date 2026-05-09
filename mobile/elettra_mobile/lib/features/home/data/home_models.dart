class HomeOverview {
  const HomeOverview({
    required this.properties,
    required this.assets,
    required this.categories,
    required this.eventsByAssetId,
    required this.remindersByAssetId,
    required this.attachmentsByAssetId,
  });

  final List<HomeProperty> properties;
  final List<HomeAsset> assets;
  final List<HomeCategory> categories;
  final Map<int, List<HomeMaintenanceEvent>> eventsByAssetId;
  final Map<int, List<HomeMaintenanceReminder>> remindersByAssetId;
  final Map<int, List<HomeAttachment>> attachmentsByAssetId;
}

class HomeCategory {
  const HomeCategory({
    required this.id,
    required this.name,
    required this.slug,
  });

  factory HomeCategory.fromJson(Map<String, dynamic> json) {
    return HomeCategory(
      id: json['id'] as int,
      name: json['name']?.toString() ?? '',
      slug: json['slug']?.toString() ?? '',
    );
  }

  final int id;
  final String name;
  final String slug;
}

class HomeProperty {
  const HomeProperty({
    required this.id,
    required this.name,
    required this.addressText,
    required this.city,
    required this.notes,
  });

  factory HomeProperty.fromJson(Map<String, dynamic> json) {
    return HomeProperty(
      id: json['id'] as int,
      name: json['name']?.toString() ?? '',
      addressText: json['address_text']?.toString() ?? '',
      city: json['city']?.toString() ?? '',
      notes: json['notes']?.toString() ?? '',
    );
  }

  final int id;
  final String name;
  final String addressText;
  final String city;
  final String notes;
}

class HomeAsset {
  const HomeAsset({
    required this.id,
    required this.propertyId,
    required this.categoryId,
    required this.name,
    required this.description,
    required this.locationText,
    required this.metadata,
  });

  factory HomeAsset.fromJson(Map<String, dynamic> json) {
    return HomeAsset(
      id: json['id'] as int,
      propertyId: json['property_id'] as int,
      categoryId: json['category_id'] as int,
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      locationText: json['location_text']?.toString() ?? '',
      metadata: Map<String, dynamic>.from(
        json['metadata_json'] as Map? ?? const {},
      ),
    );
  }

  final int id;
  final int propertyId;
  final int categoryId;
  final String name;
  final String description;
  final String locationText;
  final Map<String, dynamic> metadata;

  String? metadataValue(String key) {
    final value = metadata[key];
    if (value == null) {
      return null;
    }
    final text = value.toString().trim();
    return text.isEmpty ? null : text;
  }
}

class HomeMaintenanceEvent {
  const HomeMaintenanceEvent({
    required this.id,
    required this.assetId,
    required this.propertyId,
    required this.eventType,
    required this.title,
    required this.description,
    required this.eventDate,
  });

  factory HomeMaintenanceEvent.fromJson(Map<String, dynamic> json) {
    return HomeMaintenanceEvent(
      id: json['id'] as int,
      assetId: json['asset_id'] as int?,
      propertyId: json['property_id'] as int?,
      eventType: json['event_type']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      eventDate: DateTime.tryParse(json['event_date']?.toString() ?? ''),
    );
  }

  final int id;
  final int? assetId;
  final int? propertyId;
  final String eventType;
  final String title;
  final String description;
  final DateTime? eventDate;
}

class HomeMaintenanceReminder {
  const HomeMaintenanceReminder({
    required this.id,
    required this.assetId,
    required this.propertyId,
    required this.title,
    required this.description,
    required this.dueAt,
    required this.recurrenceRule,
    required this.status,
  });

  factory HomeMaintenanceReminder.fromJson(Map<String, dynamic> json) {
    return HomeMaintenanceReminder(
      id: json['id'] as int,
      assetId: json['asset_id'] as int?,
      propertyId: json['property_id'] as int?,
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      dueAt: DateTime.tryParse(json['due_at']?.toString() ?? ''),
      recurrenceRule: json['recurrence_rule']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
    );
  }

  final int id;
  final int? assetId;
  final int? propertyId;
  final String title;
  final String description;
  final DateTime? dueAt;
  final String recurrenceRule;
  final String status;
}

class HomeAttachment {
  const HomeAttachment({
    required this.id,
    required this.caseId,
    required this.assetId,
    required this.fileUrl,
    required this.fileName,
    required this.mimeType,
    required this.sizeBytes,
    required this.attachmentType,
    required this.createdAt,
  });

  factory HomeAttachment.fromJson(Map<String, dynamic> json) {
    return HomeAttachment(
      id: json['id'] as int,
      caseId: json['case_id'] as int?,
      assetId: json['asset_id'] as int?,
      fileUrl: json['file_url']?.toString() ?? '',
      fileName: json['file_name']?.toString() ?? '',
      mimeType: json['mime_type']?.toString() ?? '',
      sizeBytes: json['size_bytes'] as int? ?? 0,
      attachmentType: json['attachment_type']?.toString() ?? '',
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
    );
  }

  final int id;
  final int? caseId;
  final int? assetId;
  final String fileUrl;
  final String fileName;
  final String mimeType;
  final int sizeBytes;
  final String attachmentType;
  final DateTime? createdAt;
}
