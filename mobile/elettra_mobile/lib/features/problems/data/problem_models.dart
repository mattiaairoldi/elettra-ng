class CustomerProblem {
  const CustomerProblem({
    required this.id,
    required this.title,
    required this.description,
    required this.status,
    required this.priority,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CustomerProblem.fromJson(Map<String, dynamic> json) {
    return CustomerProblem(
      id: json['id'] as int,
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      priority: json['priority']?.toString() ?? '',
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  final int id;
  final String title;
  final String description;
  final String status;
  final String priority;
  final DateTime? createdAt;
  final DateTime? updatedAt;
}
