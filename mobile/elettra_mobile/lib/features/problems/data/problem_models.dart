class CustomerProblem {
  const CustomerProblem({
    required this.id,
    required this.categoryId,
    required this.propertyId,
    required this.assetId,
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
      categoryId: json['category_id'] as int? ?? 0,
      propertyId: json['property_id'] as int?,
      assetId: json['asset_id'] as int?,
      title: json['title']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      priority: json['priority']?.toString() ?? '',
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  final int id;
  final int categoryId;
  final int? propertyId;
  final int? assetId;
  final String title;
  final String description;
  final String status;
  final String priority;
  final DateTime? createdAt;
  final DateTime? updatedAt;
}

class DiagnosticChapter {
  const DiagnosticChapter({
    required this.id,
    required this.name,
    required this.description,
    required this.categoryId,
    required this.options,
  });

  factory DiagnosticChapter.fromJson(Map<String, dynamic> json) {
    final options = (json['options'] as List? ?? const [])
        .map(
          (item) =>
              DiagnosticChapterOption.fromJson(item as Map<String, dynamic>),
        )
        .toList();
    return DiagnosticChapter(
      id: json['id'] as int,
      name: json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      categoryId: json['category_id'] as int?,
      options: options,
    );
  }

  final int id;
  final String name;
  final String description;
  final int? categoryId;
  final List<DiagnosticChapterOption> options;
}

class DiagnosticChapterOption {
  const DiagnosticChapterOption({
    required this.id,
    required this.chapterId,
    required this.label,
    required this.description,
    required this.promptHint,
  });

  factory DiagnosticChapterOption.fromJson(Map<String, dynamic> json) {
    return DiagnosticChapterOption(
      id: json['id'] as int,
      chapterId: json['chapter_id'] as int? ?? 0,
      label: json['label']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      promptHint: json['prompt_hint']?.toString() ?? '',
    );
  }

  final int id;
  final int chapterId;
  final String label;
  final String description;
  final String promptHint;
}

class DiagnosticAdviceStep {
  const DiagnosticAdviceStep({
    required this.id,
    required this.chapterId,
    required this.chapterOptionId,
    required this.title,
    required this.body,
    required this.safetyLevel,
    required this.resolutionPrompt,
    required this.nextActions,
  });

  factory DiagnosticAdviceStep.fromJson(Map<String, dynamic> json) {
    return DiagnosticAdviceStep(
      id: json['id'] as int,
      chapterId: json['chapter_id'] as int? ?? 0,
      chapterOptionId: json['chapter_option_id'] as int?,
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      safetyLevel: json['safety_level']?.toString() ?? '',
      resolutionPrompt: json['resolution_prompt']?.toString() ?? '',
      nextActions: _stringList(json['next_actions_json']),
    );
  }

  final int id;
  final int chapterId;
  final int? chapterOptionId;
  final String title;
  final String body;
  final String safetyLevel;
  final String resolutionPrompt;
  final List<String> nextActions;
}

class DiagnosticFeedbackResult {
  const DiagnosticFeedbackResult({
    required this.caseId,
    required this.resolved,
    required this.caseStatus,
    required this.nextActions,
  });

  factory DiagnosticFeedbackResult.fromJson(Map<String, dynamic> json) {
    return DiagnosticFeedbackResult(
      caseId: json['case_id'] as int? ?? 0,
      resolved: json['resolved'] as bool? ?? false,
      caseStatus: json['case_status']?.toString() ?? '',
      nextActions: _stringList(json['next_actions']),
    );
  }

  final int caseId;
  final bool resolved;
  final String caseStatus;
  final List<String> nextActions;
}

class AiSessionSummary {
  const AiSessionSummary({
    required this.id,
    required this.caseId,
    required this.status,
  });

  factory AiSessionSummary.fromJson(Map<String, dynamic> json) {
    return AiSessionSummary(
      id: json['id'] as int,
      caseId: json['case_id'] as int?,
      status: json['status']?.toString() ?? '',
    );
  }

  final int id;
  final int? caseId;
  final String status;
}

class AiMessage {
  const AiMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.status,
  });

  factory AiMessage.fromJson(Map<String, dynamic> json) {
    return AiMessage(
      id: json['id'] as int,
      role: json['role']?.toString() ?? '',
      content: json['content']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
    );
  }

  final int id;
  final String role;
  final String content;
  final String status;
}

class AiDiagnosticSnapshot {
  const AiDiagnosticSnapshot({
    required this.summary,
    required this.riskLevel,
    required this.nextQuestion,
    required this.escalationRecommended,
    required this.escalationReason,
    required this.recommendation,
  });

  factory AiDiagnosticSnapshot.fromJson(Map<String, dynamic> json) {
    return AiDiagnosticSnapshot(
      summary: json['summary']?.toString() ?? '',
      riskLevel: json['risk_level']?.toString() ?? '',
      nextQuestion: json['next_question']?.toString() ?? '',
      escalationRecommended: json['escalation_recommended'] as bool? ?? false,
      escalationReason: json['escalation_reason']?.toString() ?? '',
      recommendation: json['recommendation']?.toString() ?? '',
    );
  }

  final String summary;
  final String riskLevel;
  final String nextQuestion;
  final bool escalationRecommended;
  final String escalationReason;
  final String recommendation;
}

class DiagnosticTurnResult {
  const DiagnosticTurnResult({
    required this.userMessage,
    required this.assistantMessage,
    required this.snapshot,
  });

  final AiMessage userMessage;
  final AiMessage assistantMessage;
  final AiDiagnosticSnapshot? snapshot;
}

class ProfessionalProfileSummary {
  const ProfessionalProfileSummary({
    required this.id,
    required this.displayName,
    required this.bio,
    required this.serviceAreaText,
    required this.recipientOrganizationId,
    required this.recipientMembershipId,
  });

  factory ProfessionalProfileSummary.fromJson(Map<String, dynamic> json) {
    return ProfessionalProfileSummary(
      id: json['id'] as int,
      displayName: json['display_name']?.toString() ?? '',
      bio: json['bio']?.toString() ?? '',
      serviceAreaText: json['service_area_text']?.toString() ?? '',
      recipientOrganizationId: json['recipient_organization_id'] as int?,
      recipientMembershipId: json['recipient_membership_id'] as int?,
    );
  }

  final int id;
  final String displayName;
  final String bio;
  final String serviceAreaText;
  final int? recipientOrganizationId;
  final int? recipientMembershipId;
}

class CaseShareRequestSummary {
  const CaseShareRequestSummary({
    required this.id,
    required this.status,
    required this.shareScope,
  });

  factory CaseShareRequestSummary.fromJson(Map<String, dynamic> json) {
    return CaseShareRequestSummary(
      id: json['id'] as int,
      status: json['status']?.toString() ?? '',
      shareScope: json['share_scope']?.toString() ?? '',
    );
  }

  final int id;
  final String status;
  final String shareScope;
}

List<String> _stringList(Object? value) {
  if (value is List) {
    return value
        .map(_stringValue)
        .where((item) => item.trim().isNotEmpty)
        .toList();
  }
  if (value is Map) {
    return value.values
        .map(_stringValue)
        .where((item) => item.trim().isNotEmpty)
        .toList();
  }
  return const [];
}

String _stringValue(Object? value) {
  if (value is Map) {
    return (value['label'] ?? value['title'] ?? value['code'] ?? '').toString();
  }
  return value?.toString() ?? '';
}
