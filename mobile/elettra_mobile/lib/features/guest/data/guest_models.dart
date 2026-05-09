import '../../problems/data/problem_models.dart';

class GuestQuota {
  const GuestQuota({
    required this.aiTurnLimit,
    required this.aiTurnsUsed,
    required this.aiTurnsRemaining,
    required this.messageLimit,
    required this.messagesUsed,
    required this.messagesRemaining,
  });

  factory GuestQuota.fromJson(Map<String, dynamic> json) {
    return GuestQuota(
      aiTurnLimit: json['ai_turn_limit'] as int? ?? 0,
      aiTurnsUsed: json['ai_turns_used'] as int? ?? 0,
      aiTurnsRemaining: json['ai_turns_remaining'] as int? ?? 0,
      messageLimit: json['message_limit'] as int? ?? 0,
      messagesUsed: json['messages_used'] as int? ?? 0,
      messagesRemaining: json['messages_remaining'] as int? ?? 0,
    );
  }

  final int aiTurnLimit;
  final int aiTurnsUsed;
  final int aiTurnsRemaining;
  final int messageLimit;
  final int messagesUsed;
  final int messagesRemaining;
}

class GuestSessionSummary {
  const GuestSessionSummary({
    required this.id,
    required this.token,
    required this.status,
    required this.expiresAt,
    required this.quotas,
  });

  factory GuestSessionSummary.fromJson(Map<String, dynamic> json) {
    return GuestSessionSummary(
      id: json['guest_session_id']?.toString() ?? '',
      token: json['guest_token']?.toString(),
      status: json['status']?.toString() ?? '',
      expiresAt: DateTime.tryParse(json['expires_at']?.toString() ?? ''),
      quotas: GuestQuota.fromJson(
        json['quotas'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }

  final String id;
  final String? token;
  final String status;
  final DateTime? expiresAt;
  final GuestQuota quotas;
}

class GuestCallToAction {
  const GuestCallToAction({
    required this.code,
    required this.title,
    required this.message,
    required this.actionLabel,
  });

  factory GuestCallToAction.fromJson(Map<String, dynamic> json) {
    return GuestCallToAction(
      code: json['code']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      actionLabel: json['action_label']?.toString() ?? 'Accedi',
    );
  }

  final String code;
  final String title;
  final String message;
  final String actionLabel;

  bool get isEmpty => code.isEmpty && title.isEmpty && message.isEmpty;
}

class GuestDiagnosticResult {
  const GuestDiagnosticResult({
    required this.adviceSteps,
    required this.userMessage,
    required this.assistantMessage,
    required this.snapshot,
    required this.quotas,
    required this.callToAction,
  });

  factory GuestDiagnosticResult.fromJson(Map<String, dynamic> json) {
    final ctaPayload = json['call_to_action'];
    return GuestDiagnosticResult(
      adviceSteps: (json['advice_steps'] as List? ?? const [])
          .map(
            (item) =>
                DiagnosticAdviceStep.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
      userMessage: _messageFromJson(json['user_message']),
      assistantMessage: _messageFromJson(json['assistant_message']),
      snapshot: _snapshotFromJson(json['diagnostic_snapshot']),
      quotas: GuestQuota.fromJson(
        json['quotas'] as Map<String, dynamic>? ?? const {},
      ),
      callToAction: ctaPayload is Map<String, dynamic>
          ? GuestCallToAction.fromJson(ctaPayload)
          : const GuestCallToAction(
              code: '',
              title: '',
              message: '',
              actionLabel: 'Accedi',
            ),
    );
  }

  final List<DiagnosticAdviceStep> adviceSteps;
  final AiMessage? userMessage;
  final AiMessage? assistantMessage;
  final AiDiagnosticSnapshot? snapshot;
  final GuestQuota quotas;
  final GuestCallToAction callToAction;
}

AiMessage? _messageFromJson(Object? value) {
  if (value is Map<String, dynamic>) {
    return AiMessage.fromJson(value);
  }
  return null;
}

AiDiagnosticSnapshot? _snapshotFromJson(Object? value) {
  if (value is Map<String, dynamic>) {
    return AiDiagnosticSnapshot.fromJson(value);
  }
  return null;
}
